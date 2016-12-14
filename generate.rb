#!/usr/bin/env ruby

require 'yaml'

# load default file
packages = YAML.load_file('mockup.yaml')

require 'pp'
pp packages.inspect

packages.keys.sort.each do |pkg|
  packages[pkg].keys.sort.each do |d|
    puts "#{pkg} depends on #{d}"
  end

end
