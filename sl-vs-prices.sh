#!/bin/sh
#
#   Get list of prices of sl vertual server (cci)
#   Last modified by NAKAJIMA Takaaki on May 22, 2014.
#

cpus="1 2 4 8"
memories="1024 2048 4096 6144 8192 12288 16384 32768 49152 65536"
oses="CENTOS DEBIAN REDHAT UBUNTU VYATTACE WIN"

for os in $oses
do
  os_type=${os}_LATEST
  for cpu in $cpus
  do
    for memory in $memories
    do
      for period in hourly monthly
      do
        ofile=sl-vs-price-${os_type}_${cpu}_${memory}_${period}.txt
        if [ ! -f $ofile ]
        then
          sl cci create --test \
              --hostname=test_${os_type}_${cpu}_${memory} \
              --domain=example.com \
              --cpu=$cpu --memory=$memory \
              --os=${os_type} --${period} > $ofile
          date >>$ofile
        fi
        cost=$( egrep "^Total ${period} cost" $ofile | \
                sed -e "s/^Total ${period} cost *//" )
        if [ "x$os" = "xVYATTACE" ]
        then
          os_name=$( egrep -i Vyatta $ofile | \
                     sed -e 's/ *[0-9]*\.[0-9]* *$//' )
        elif [ "x$os" = "xREDHAT" ]
        then
          os_name=$( egrep -i "Red Hat" $ofile | \
                     sed -e 's/ *[0-9]*\.[0-9]* *$//' )
        else
          os_name=$( egrep -i $os $ofile | \
                     sed -e 's/ *[0-9]*\.[0-9]* *$//' )
        fi
        echo \"$os_name\",$cpu,$memory,$period,$cost
      done
    done
  done
done
