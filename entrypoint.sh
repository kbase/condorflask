mkdir -p /etc/condor/
if [ "${POOL_PASSWORD}" ] ; then
  /usr/sbin/condor_store_cred -p "${POOL_PASSWORD}" -f /etc/condor/password
fi
chmod +x rungunicorn && ./rungunicorn
