-- Airquality log
--
create table airquality (
 dt timestamp with time zone not null default now(),
 sensor varchar(32) not null,
 pm01d0 float not null,
 pm02d5 float not null,
 pm04d0 float not null,
 pm10d0 float not null,
 nc00d5 float not null,
 nc01d0 float not null,
 nc02d5 float not null,
 nc04d0 float not null,
 nc10d0 float not null,
 tps float  not null,
 unique(dt, sensor)
);

-- Sensor status log
create table sensorlog (
 dt timestamp with time zone not null default now(),
 sensor varchar(32) not null,
 uptime float,
 temperature float,
 unique(dt, sensor)
);

-- Sensor information table
create table sensors (
 sensor varchar(32) not null primary key,
 idn smallint,
 status smallint not null default 0,
 activated timestamp with time zone not null default now(),
 note text,
 lat float,
 lon float,
 height float,
 unique(sensor, idn, activated)
);

