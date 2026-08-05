[out:json][timeout:90];
(
  way["highway"~"^(primary|secondary|tertiary)$"](16.035,108.190,16.090,108.250);
  node["amenity"="hospital"](16.035,108.190,16.090,108.250);
  way["amenity"="hospital"](16.035,108.190,16.090,108.250);
  relation["amenity"="hospital"](16.035,108.190,16.090,108.250);
);
(._;>;);
out body;
