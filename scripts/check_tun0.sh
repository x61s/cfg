#bin/bash

for i in tun0
  do RESULT="$(ip link ls $i up 2>&1)";

    if [[ $RESULT == *"does not exist."* ]]; then
      exit 1
    else
      echo "tun0 $(ip -4 addr show dev tun0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')"
    fi

done
