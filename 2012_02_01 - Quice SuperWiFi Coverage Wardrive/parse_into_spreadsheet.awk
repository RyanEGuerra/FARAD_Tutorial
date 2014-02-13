#!/bin/awk
BEGIN{
}
{
	# Capture data fields from raw log file
	rate = $4;
	freq = $6;
	rssi = $9;;
	src = $16;
	proto = $19;
	len = $21;
	lat = $23;
	lon = $25;
	alt = $27;

	# Clean data fields
	rssi = substr(rssi, 1, length(rssi)-2);
	
	split(src, a, ".");
	src = a[4];

	proto = substr(proto, 1, length(proto)-1);

	filename = sprintf("tower_%s.csv", src);

	# Print fields in CSV format
	printf("%s, %s, %s, %s, %s, %s, %s, %s\n",
			lon, lat, alt, rssi, rate, freq, len, src) > filename;
}
END{
	
}
