PARA PROBAR QUE FUNCIONE

primero en la bodega de datos ejecutar el este script:

DROP TABLE IF EXISTS fact_servicio CASCADE;
DROP TABLE IF EXISTS dim_sede CASCADE;
DROP TABLE IF EXISTS dim_mensajero CASCADE;
DROP TABLE IF EXISTS dim_cliente CASCADE;
DROP TABLE IF EXISTS dim_fechahora CASCADE;

CREATE TABLE dim_mensajero (
	mensajero_key BIGINT NOT NULL,
	mensajero_id BIGINT NOT NULL,
	nombre_completo VARCHAR(80),

	PRIMARY KEY (mensajero_key)
);


CREATE TABLE dim_cliente (
	cliente_key BIGINT NOT NULL,
	cliente_id BIGINT NOT NULL,
	nit_cliente VARCHAR(30),
	nombre_cliente VARCHAR(120),
	sector VARCHAR(80),
	tipo_cliente VARCHAR(80),
	ciudad_principal VARCHAR(80),
	estado_activo BOOL,

	PRIMARY KEY (cliente_key)
);

CREATE TABLE dim_fechahora (
	fecha_hora_key BIGINT NOT NULL,
	fecha_hora TIMESTAMP,
	año FLOAT,
	mes FLOAT,
	minuto FLOAT,
	dia FLOAT,
	hora FLOAT,
	dia_de_la_semana VARCHAR(20),

	PRIMARY KEY (fecha_hora_key)
);


CREATE TABLE dim_sede (
    sede_key INTEGER NOT NULL,
    sede_id BIGINT NOT NULL,
    nombre VARCHAR(80),
    fk_cliente INTEGER NOT NULL,

    PRIMARY KEY (sede_key),
    FOREIGN KEY (fk_cliente)
        REFERENCES dim_cliente(cliente_key)
);

CREATE TABLE fact_servicio (
	servicio_id BIGINT NOT NULL,
	fk_fecha_iniciado BIGINT NOT NULL,
	fk_fecha_asignado BIGINT,
	fk_fecha_recogido BIGINT,
	fk_fecha_entregado BIGINT,
	fk_fecha_cerrado BIGINT,
	fk_cliente BIGINT NOT NULL,
	fk_mensajero BIGINT,
	fk_sede BIGINT,

	PRIMARY KEY(servicio_id),
	FOREIGN KEY (fk_fecha_iniciado) REFERENCES dim_fechahora(fecha_hora_key),
	FOREIGN KEY (fk_fecha_asignado) REFERENCES dim_fechahora(fecha_hora_key),
	FOREIGN KEY (fk_fecha_recogido) REFERENCES dim_fechahora(fecha_hora_key),
	FOREIGN KEY (fk_fecha_entregado) REFERENCES dim_fechahora(fecha_hora_key),
	FOREIGN KEY (fk_fecha_cerrado) REFERENCES dim_fechahora(fecha_hora_key),
	FOREIGN KEY (fk_cliente) REFERENCES dim_cliente(cliente_key),
	FOREIGN KEY (fk_mensajero) REFERENCES dim_mensajero(mensajero_key),
	FOREIGN KEY (fk_sede) REFERENCES dim_sede(sede_key)
)

