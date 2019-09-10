  useradd kbase
  if [ "${POOL_PASSWORD}" ] ; then
        /usr/sbin/condor_store_cred -p "${POOL_PASSWORD}" -f /etc/condor/password
  fi
  chown kbase /etc/condor/password
  
  chmod +x rungunicorn && ./rungunicorn
