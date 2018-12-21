CREATE EXTENSION postgis;

CREATE SCHEMA sit_example
  AUTHORIZATION sit_example;

GRANT ALL ON SCHEMA sit_example TO sit_example;

CREATE TABLE sit_example.portal
(
  id serial NOT NULL,
  codi integer NOT NULL,
  numero character varying(10) NOT NULL,
  lletra character varying(10),
  numero_extrem boolean NOT NULL,
  estat character varying(25),
  data_baixa timestamp with time zone,
  the_geom geometry(Point,25831) NOT NULL,
  codi_carrer integer,
  codi_edifici integer,
  CONSTRAINT portal_pkey PRIMARY KEY (id),
  CONSTRAINT portal_codi_key UNIQUE (codi)
);

ALTER TABLE sit_example.portal
  OWNER TO sit_example;
GRANT ALL ON TABLE sit_example.portal TO sit_example;

CREATE INDEX portal_2376b1e9
  ON sit_example.portal
  USING btree
  (codi_carrer);

CREATE INDEX portal_2376b1e8
  ON sit_example.portal
  USING btree
  (codi_edifici);

CREATE INDEX portal_the_geom_id
  ON sit_example.portal
  USING gist
  (the_geom);


  CREATE TABLE sit_example.carrer
  (
    id serial NOT NULL,
    codi integer NOT NULL,
    nom character varying(10) NOT NULL,
    the_geom geometry(MultiLineString,25831) NOT NULL,
    CONSTRAINT carrer_pkey PRIMARY KEY (id),
    CONSTRAINT carrer_codi_key UNIQUE (codi)
  );

  ALTER TABLE sit_example.carrer
    OWNER TO sit_example;
  GRANT ALL ON TABLE sit_example.portal TO sit_example;


  CREATE INDEX carrer_the_geom_id
    ON sit_example.carrer
    USING gist
    (the_geom);
