#!/usr/bin/env ruby

# this script will generate all necessary meta-packages (rpm and deb)
# based on the main config file and what is already present under the
# target directory

require 'yaml'

# where to find meta information about packages
meta_dir = 'meta'

# where to stage packages - will create this one and RPM/DEB dirs underneath
stage_dir = 'stage'

# load default file
packages = YAML.load_file("#{meta_dir}/all.yml")

require 'pp'
pp packages.inspect


packages.keys.sort.each do |pkg|
  packages[pkg].keys.sort.each do |d|
    puts "#{pkg} depends on #{d}"
  end

end
