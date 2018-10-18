#!/usr/bin/env ruby

# this script will generate all necessary meta-packages (rpm and deb)
# based on the main config file and what is already present under the
# target directory

require 'pp'
require 'date'
require 'fileutils'
require 'yaml'

# store path of this script
ROOT = File.expand_path(__dir__).freeze

# standard directory layout (relative to $ROOT)
# meta/ contains the meta package definitions - one per file
# stage/pkgname/{deb,rpm}/ contain all necessary information to build meta-packages

def rpm_create_source(pkg_data)
  spec = File.open("#{ROOT}/stage/#{pkg_data['name']}/rpm/#{pkg_data['name']}.spec", 'w')
  spec.puts <<-SPECSTART
Name: #{pkg_data['name']}
Version: #{pkg_data['changelog'][0]['version']}
Release: 1%{?dist}
License: GPLv3+
URL: https://git.ligo.org/packaging/lscsoft-metapackages
Summary: #{pkg_data['desc_short']}
BuildArch: noarch
SPECSTART

  # if extra headers are specified, add them verbatim here
  if pkg_data.key?('extra_headers') && pkg_data['extra_headers'].key?('rpm')
    pkg_data['extra_headers']['rpm'].each do |h|
      spec.puts h
    end
  end

  # add dependencies
  dep_list = []

  pkg_data['deps'].each do |k,v|
    # add key as package name if value is nil (simple package, same for deb and rpm)
    if v.nil?
      dep_list << k
    # if our key (rpm/deb) exists use its value or the package name itself if value is empty
    elsif v.key?('rpm')
      dep_list << ( v['rpm'].nil? ? k : v['rpm'] )
    end
  end

  # write out Requires block
  spec.puts
  dep_list.sort.each do |d|
    spec.puts "Requires: #{d}"
  end

  spec.puts <<-SPECMID

%description
#{pkg_data['desc_long'].strip}

%prep

%build

%install

%files

%changelog
SPECMID
  pkg_data['changelog'].each do |entry|
    spec.puts "* #{entry['date'].strftime('%a %b %e %Y')} #{entry['author']} #{entry['version']}-1"
    entry['changes'].each do |item|
      indent = '- '
      # this can be a multiline string from YAML, hence
      # - split on newline
      # - add '- ' to first and
      # - '  'to every other line
      item.split("\n").each do |line|
        spec.puts indent + line
        indent = '  '
      end
    end
  end
end

def reformat_wrapped(s, width = 78)
  # helper function needed to reformat long description
  # based on https://www.safaribooksonline.com/library/view/ruby-cookbook/0596523696/ch01s15.html
  # other solution, thanks AlexP
  # .gsub("\n\n", "\n.\n").scan(/\S.{0,#{width-2}}\S(?=\s|$)|\S+/).collect {|x| " " + x }.join("\n")
  parts = []
  s.split(/\n\n/).each do |part|
    lines = []
    line = ''
    part.split(/\s+/).each do |word|
      if line.size + word.size >= width
        lines << line
        line = word
      elsif line.empty?
        line = word
      else
        line << ' ' << word
      end
    end
    lines << line if line
    parts << ' ' + (lines.join "\n ")
  end
  parts.join "\n .\n"
end

def deb_create_source(pkg_data)
  deb_control(pkg_data)
  deb_readme(pkg_data)
  deb_changelog(pkg_data)
  deb_copyright(pkg_data)
end

def deb_readme(pkg_data)
  # create README
  readme = File.new("#{ROOT}/stage/#{pkg_data['name']}/deb/README", 'w')
  readme.puts pkg_data['desc_long']
  readme.close
end

def deb_changelog(pkg_data)
  # create changelog
  changelog = File.new("#{ROOT}/stage/#{pkg_data['name']}/deb/changelog.Debian", 'w')
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

def deb_copyright(pkg_data)
  # create 'copyright'
  copyright = File.new("#{ROOT}/stage/#{pkg_data['name']}/deb/copyright", 'w')
  copyright.puts <<-COPYRIGHT
Upstream Author(s): The LIGO Scientific Collaboration

Copyright: LIGO Scientific Collaboration

License: GPLv2 (or later)
COPYRIGHT
  copyright.close
end

def deb_control(pkg_data)
  # create control file
  control = File.new("#{ROOT}/stage/#{pkg_data['name']}/deb/control", 'w')

  # start with simple header
  control.puts <<-CONTROLSTART
Section: #{pkg_data['section']}
Priority: #{pkg_data['priority']}
Standards-Version: 3.9.8
Package: #{pkg_data['name']}
Maintainer: #{pkg_data['maintainer']}
Readme: README
Changelog: changelog.Debian
Copyright: copyright
Architecture: all
CONTROLSTART

  # if extra headers are specified, add them verbatim here
  if pkg_data.key?('extra_headers') && pkg_data['extra_headers'].key?('deb')
    pkg_data['extra_headers']['deb'].each do |h|
      control.puts h
    end
  end

  # add dependencies
  dep_list = []
  pkg_data['deps'].each do |k, v|
    # add key as package name if value is nil (simple package, same for deb and rpm)
    if v.nil?
      dep_list << k
    # if our key (rpm/deb) exists use its value or the package name itself if value is empty
    elsif v.key?('deb')
      dep_list << (v['deb'].nil? ? k : v['deb'])
    end
  end

  # write out dependency block
  dep_list.sort.each do |d|
    control.puts "Depends: #{d}"
  end
  control.puts <<-CONTROLEND

Description: #{pkg_data['desc_short']}
#{reformat_wrapped(pkg_data['desc_long'])}
CONTROLEND
  control.close
end

############# MAIN

# iterate over each file in meta/
Dir.glob("#{ROOT}/meta/*.yml") do |meta_file|
  puts "Working on: #{meta_file}"

  pkg = meta_file[/^#{ROOT}\/meta\/(.+)\.yml$/, 1]
  content = YAML.load_file(meta_file)

  # a few modifications need to be done (convenience)
  # parse date/times from changelog and sort them with newest first
  content['changelog'].each do |entry|
    entry['date'] = DateTime.parse(entry['date'].to_s)
  end
  content['changelog'].sort! { |x, y| y['date'] <=> x['date'] }

  # add package name (inferred from YAML fname)
  content['name'] = pkg
  # add long description unless given
  content['desc_long'] = content['desc_short'] if content['desc_long'].nil?

  # basic tests
  %w[changelog desc_short desc_long deps name maintainer priority section].each do |t|
    raise "#{meta_file} requires key '#{t}'" unless content.key?(t)
  end
  # ensure target dirs are is present
  %w[deb rpm].each do |d|
    FileUtils.mkpath("#{ROOT}/stage/#{pkg}/#{d}")
  end

  # once we get here, check if we need to work at all on this one
  # for that, check its version file and compare to latest one from changelog
  last_version = "#{ROOT}/stage/#{pkg}/version"
  if File.exist?(last_version)
    version = File.open(last_version, &:gets)
    next if version.to_s.chomp.eql?(content['changelog'][0]['version'].to_s.chomp)
  end

  # create rpm source package
  rpm_create_source(content)

  # create deb source package
  deb_create_source(content)

  # all done, then update version file
  version = File.open(last_version, 'w')
  version.puts content['changelog'][0]['version'].to_s
  version.close
end
