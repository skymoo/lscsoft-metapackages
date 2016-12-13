#!/usr/bin/env ruby

# systems to collect data from (need to be able to gsissh into those)
yum_host = 'ldas-grid.ligo.caltech.edu'
apt_host = 'atlas6.atlas.aei.uni-hannover.de'

# get data fro yum host first
IO.popen("gsissh #{yum_host} yum list") do |line|
  next unless line =~ /^lscsoft/
  puts line
end
