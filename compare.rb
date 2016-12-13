#!/usr/bin/env ruby

# systems to collect data from (need to be able to gsissh into those)
yum_host = 'ldas-grid.ligo.caltech.edu'
apt_host = 'atlas6.atlas.aei.uni-hannover.de'

packages = {}

#### YUM ####
# get data from yum host first
IO.popen("gsissh #{yum_host} yum list").each do |line|
  next unless line =~ /^lscsoft/
  # remove trailing stuff after dot from package name
  tmp = line.split
  tmp[0].gsub! /\.\S+/, ''
  packages[tmp[0]] = { yum_version: tmp[1] }
end

# now query each metapackage for dependencies
cur_package = ''
IO.popen("gsissh #{yum_host} yum deplist #{packages.keys.join(' ')}").each do |line|
  line.chomp!
  if line =~ /package:/
    cur_package = line.split[1].gsub! /\.\S+/, ''
  elsif line =~ /dependency:/
    line.gsub! /^.+dependency:\s*/, ''
    ( packages[cur_package][:yum_deps] ||= [] ) << line
  end
end

#### APT ####
# get data from apt host
IO.popen("gsissh #{apt_host} dpkg -l").each do |line|
  next unless line =~ /^ii\s+lscsoft/
  tmp = line.split
  packages[tmp[1]] ||= {}
  packages[tmp[1]][:apt_version] = tmp[2]
end

IO.popen("gsissh #{apt_host} apt-cache depends #{packages.keys.find_all { |k| packages[k].has_key? :apt_version}.join(' ')}").each do |line|
  line.chomp!
  if line =~ /^lscsoft/
    cur_package = line
  elsif line =~ /Depends:/
    line.gsub! /^.+Depends:\s*/, ''
    ( packages[cur_package][:apt_deps] ||= [] ) << line
  end
end


require 'pp'
pp packages
