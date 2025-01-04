# This script gets a data file and signature file.
# It should return true if the data file is signed with valid authorized
# signature. 
data=$1
sig=$2
if c=$(ssh-keygen -Y check-novalidate -n file -s $sig <$data)
then
  # Here it only checks that the file is signed with a valid signature.
  # whether or not this signature belongs to a trusted correspondent is not
  # verified here.
  c=${c##*RSA key }
  echo $c
  # TODO verify that signature belongs to one of the authorized identities.
  exit 0
else
  echo "invalid"
  exit 255
fi
