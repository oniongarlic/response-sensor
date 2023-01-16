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
create table sensor (
 dt timestamp with time zone not null default now(),
 sensor varchar(32) not null,
 uptime float,
 temperature float,
 unique(dt, sensor)
);
