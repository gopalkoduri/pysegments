for i in *; do for j in "$i"/10/*; do mv "$j" "`echo $j|sed 's/\//\_/g'`"; done; done
