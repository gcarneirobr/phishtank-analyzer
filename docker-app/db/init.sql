    -- Database: phishtank

    -- DROP DATABASE phishtank;

     CREATE DATABASE phishtank
        WITH 
        OWNER = postgres
        ENCODING = 'UTF8'
        LC_COLLATE = 'en_US.utf8'
        LC_CTYPE = 'en_US.utf8'
        TABLESPACE = pg_default
        CONNECTION LIMIT = -1;

    -- Table: public.phish
    
    -- DROP TABLE public.phish;
    -- Table: public.phish

    -- DROP TABLE public.phish;

   -- Table: public.phish

-- DROP TABLE public.phish;

CREATE TABLE public.phish
(
    id integer NOT NULL,
    phish_id integer NOT NULL,
    url character varying(5000) COLLATE pg_catalog."default" NOT NULL,
    verified character varying(3) COLLATE pg_catalog."default" NOT NULL,
    online boolean NOT NULL,
    target character varying(100) COLLATE pg_catalog."default" NOT NULL,
    details_ip_address character varying(20) COLLATE pg_catalog."default" NOT NULL,
    details_cidr_block character varying(20) COLLATE pg_catalog."default",
    details_announcing_network character varying(50) COLLATE pg_catalog."default",
    details_rir character varying(50) COLLATE pg_catalog."default",
    hash character varying(100) COLLATE pg_catalog."default",
    submission_time timestamp with time zone,
    valid_until timestamp with time zone,
    detail_time timestamp with time zone,
    verification_time timestamp with time zone,
    crawler_verified boolean DEFAULT false,
    CONSTRAINT phish_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.phish
    OWNER to root;
    -- SEQUENCE: public.phish_sequence

    -- DROP SEQUENCE public.phish_sequence;

    CREATE SEQUENCE IF NOT EXISTS public.phish_sequence;

    ALTER SEQUENCE public.phish_sequence
        OWNER TO root;