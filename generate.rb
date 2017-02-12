#!/usr/bin/env ruby

# this script will generate all necessary meta-packages (rpm and deb)
# based on the main config file and what is already present under the
# target directory

require 'yaml'

$ROOT = '/home/carsten/PROJECTS/LIGO/lscsoft-metapackage-comparison'
# standard directory layout:
# meta/ contains the meta package definitions - one per file
# stage/{deb,rpm}/ contain all necessary information to build meta-packages
# results/ if we can somehow figure out how to build all packages on the host
# machine, this directory shall contain the resulting packages
require 'pp'
require 'date'
require 'fileutils'

def deb_create_source(fname, pkg_data)
  # basic tests
  %w(changelog desc_short desc_long deps name maintainer priority section).each do |t|
    raise "#{fname} requires key '#{t}'" unless pkg_data.key?(t)
  end

  # ensure target dir is present
  FileUtils.mkpath("#{$ROOT}/stage/deb/#{pkg_data['name']}")

  # check if we need to act at all
  # if 'changelog.Debian' does not exist --> act
  # first version line in 'changelog.Debian' contains our latest version string -> return
  # otherwise --> act

  changelog_file = "#{$ROOT}/stage/deb/#{pkg_data['name']}/changelog.Debian"
  if File.exist?(changelog_file)
    File.open(changelog_file).each do |l|
      next unless l =~ /^\S+ \(([a-zA-Z0-9.+-:]+)\) /
      return if $1.to_s.eql? pkg_data['changelog'][0]['version'].to_s
      break
    end
  end
  deb_control(fname, pkg_data)
  deb_readme(fname, pkg_data)
  deb_changelog(fname, pkg_data)
  deb_copyright(fname, pkg_data)
end

def deb_readme(fname, pkg_data)
# create README
  readme = File.new("#{$ROOT}/stage/deb/#{pkg_data['name']}/README", 'w')
  readme.puts pkg_data['desc_long']
  readme.close
end

def deb_changelog(fname, pkg_data)
# create changelog
  changelog = File.new("#{$ROOT}/stage/deb/#{pkg_data['name']}/changelog.Debian", 'w')
  pkg_data['changelog'].each do |entry|
    changelog.puts "#{pkg_data['name']} (#{entry['version']}) unstable; urgency=medium\n\n"
    entry['changes'].each do |item|
      indent = '  * '
      # this can be a multiline string from YAML, hence
      # - split on newline
      # - add '  * ' to first and
      # - '    ' to every other line
      item.split("\n").each do |line|
        changelog.puts indent + line + "\n"
        indent = '    '
      end
      changelog.puts
    end
    changelog.puts " -- #{entry['author']}  #{entry['date'].strftime('%a, %d %b %Y %H:%M:%S %z')}\n\n"
  end

  changelog.close
end
def deb_copyright(fname, pkg_data)
# create 'copyright'
  copyright = File.new("#{$ROOT}/stage/deb/#{pkg_data['name']}/copyright", 'w')
  copyright.puts <<-COPYRIGHT
Upstream Author(s): The LIGO Scientific Collaboration

Copyright: LIGO Scientific Collaboration

License: GPLv2 (or later)
COPYRIGHT
  copyright.close
end

def deb_control(fname, pkg_data)
  # create control file
  control = File.new("#{$ROOT}/stage/deb/#{pkg_data['name']}/control", 'w')

  # start with simple header
  control.puts <<-CONTROLSTART
Section: #{pkg_data['section']}
Priority: #{pkg_data['priority']}
Standards-Version: 3.9.2

Package: #{pkg_data['name']}
Maintainer: #{pkg_data['maintainer']}
Readme: README
Changelog: changelog.Debian
Copyright: copyright
Architecture: all
CONTROLSTART

  # add dependencies
  dep_list = []
  pkg_data['deps'].each do |k,v|
    # simple, unversioned dependencies only list 'nil' as a value
    if v.nil?
      dep_list << k
      next
    end

    # in any other case a deb hash key must be present
    raise "#{fname}:\n  versioned dependency for package #{pkg_data['name']}: #{k} requires 'deb' key" unless v.key?('deb')
    dep_list << "#{k} (#{v['deb']})"
  end
  control.puts 'Depends: ' + dep_list.sort.join(', ')
  control.puts <<-CONTROLEND
Description: #{pkg_data['desc_short']}
 #{pkg_data['desc_long']}
CONTROLEND
  control.close

end
# iterate over each file in meta/
Dir.glob("#{$ROOT}/meta/*.yml") do |meta_file|
  puts meta_file
  pkg = meta_file[/^#{$ROOT}\/meta\/(.+)\.yml$/,1]
  content = YAML.load_file(meta_file)

  # a few modifications need to be done (convenience)
  # parse date/times from changelog and sort them with newest first
  content['changelog'].each do |entry|
    entry['date'] = DateTime.parse(entry['date'].to_s)
  end
  content['changelog'].sort!{ |x,y| y['date'] <=> x['date'] }

  # add package name (inferred from YAML fname)
  content['name'] = pkg
  # add long description unless given
  content['desc_long'] = content['desc_short'] if content['desc_long'].nil?

  # create deb source package
  deb_create_source(meta_file, content)
end
