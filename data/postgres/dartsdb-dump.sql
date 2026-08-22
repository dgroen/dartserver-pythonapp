--
-- PostgreSQL database dump
--

\restrict bcThKSGb4CZigPvoTYKu46GdmxyfZDqjOWaHcsdpW3ZHR36JOIgxMcWbHCI641I

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.training_session DROP CONSTRAINT IF EXISTS training_session_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.training_session DROP CONSTRAINT IF EXISTS training_session_game_type_id_fkey;
ALTER TABLE IF EXISTS ONLY public.training_score DROP CONSTRAINT IF EXISTS training_score_training_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.training_score DROP CONSTRAINT IF EXISTS training_score_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scores DROP CONSTRAINT IF EXISTS scores_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scores DROP CONSTRAINT IF EXISTS scores_game_result_id_fkey;
ALTER TABLE IF EXISTS ONLY public.hotspot_config DROP CONSTRAINT IF EXISTS hotspot_config_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.gameresults DROP CONSTRAINT IF EXISTS gameresults_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.gameresults DROP CONSTRAINT IF EXISTS gameresults_game_type_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dartboard_zone_mapping DROP CONSTRAINT IF EXISTS dartboard_zone_mapping_dartboard_type_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dartboard DROP CONSTRAINT IF EXISTS dartboard_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.apikey DROP CONSTRAINT IF EXISTS apikey_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.api_key DROP CONSTRAINT IF EXISTS api_key_player_id_fkey;
DROP INDEX IF EXISTS public.ix_player_username;
DROP INDEX IF EXISTS public.ix_player_email;
DROP INDEX IF EXISTS public.ix_dartboard_zone_mapping_dartboard_type_id;
DROP INDEX IF EXISTS public.ix_dartboard_dartboard_id;
DROP INDEX IF EXISTS public.ix_api_key_key_hash;
ALTER TABLE IF EXISTS ONLY public.training_session DROP CONSTRAINT IF EXISTS training_session_session_id_key;
ALTER TABLE IF EXISTS ONLY public.training_session DROP CONSTRAINT IF EXISTS training_session_pkey;
ALTER TABLE IF EXISTS ONLY public.training_score DROP CONSTRAINT IF EXISTS training_score_pkey;
ALTER TABLE IF EXISTS ONLY public.scores DROP CONSTRAINT IF EXISTS scores_pkey;
ALTER TABLE IF EXISTS ONLY public.player DROP CONSTRAINT IF EXISTS player_pkey;
ALTER TABLE IF EXISTS ONLY public.hotspot_config DROP CONSTRAINT IF EXISTS hotspot_config_pkey;
ALTER TABLE IF EXISTS ONLY public.gametype DROP CONSTRAINT IF EXISTS gametype_pkey;
ALTER TABLE IF EXISTS ONLY public.gametype DROP CONSTRAINT IF EXISTS gametype_name_key;
ALTER TABLE IF EXISTS ONLY public.gameresults DROP CONSTRAINT IF EXISTS gameresults_pkey;
ALTER TABLE IF EXISTS ONLY public.dartboard_zone_mapping DROP CONSTRAINT IF EXISTS dartboard_zone_mapping_pkey;
ALTER TABLE IF EXISTS ONLY public.dartboard_type DROP CONSTRAINT IF EXISTS dartboard_type_pkey;
ALTER TABLE IF EXISTS ONLY public.dartboard_type DROP CONSTRAINT IF EXISTS dartboard_type_name_key;
ALTER TABLE IF EXISTS ONLY public.dartboard DROP CONSTRAINT IF EXISTS dartboard_pkey;
ALTER TABLE IF EXISTS ONLY public.apikey DROP CONSTRAINT IF EXISTS apikey_pkey;
ALTER TABLE IF EXISTS ONLY public.apikey DROP CONSTRAINT IF EXISTS apikey_api_key_key;
ALTER TABLE IF EXISTS ONLY public.api_key DROP CONSTRAINT IF EXISTS api_key_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.training_session ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.training_score ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.scores ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.player ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.hotspot_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.gametype ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.gameresults ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dartboard_zone_mapping ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dartboard_type ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dartboard ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.apikey ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.api_key ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.training_session_id_seq;
DROP TABLE IF EXISTS public.training_session;
DROP SEQUENCE IF EXISTS public.training_score_id_seq;
DROP TABLE IF EXISTS public.training_score;
DROP SEQUENCE IF EXISTS public.scores_id_seq;
DROP TABLE IF EXISTS public.scores;
DROP SEQUENCE IF EXISTS public.player_id_seq;
DROP TABLE IF EXISTS public.player;
DROP SEQUENCE IF EXISTS public.hotspot_config_id_seq;
DROP TABLE IF EXISTS public.hotspot_config;
DROP SEQUENCE IF EXISTS public.gametype_id_seq;
DROP TABLE IF EXISTS public.gametype;
DROP SEQUENCE IF EXISTS public.gameresults_id_seq;
DROP TABLE IF EXISTS public.gameresults;
DROP SEQUENCE IF EXISTS public.dartboard_zone_mapping_id_seq;
DROP TABLE IF EXISTS public.dartboard_zone_mapping;
DROP SEQUENCE IF EXISTS public.dartboard_type_id_seq;
DROP TABLE IF EXISTS public.dartboard_type;
DROP SEQUENCE IF EXISTS public.dartboard_id_seq;
DROP TABLE IF EXISTS public.dartboard;
DROP SEQUENCE IF EXISTS public.apikey_id_seq;
DROP TABLE IF EXISTS public.apikey;
DROP SEQUENCE IF EXISTS public.api_key_id_seq;
DROP TABLE IF EXISTS public.api_key;
DROP TABLE IF EXISTS public.alembic_version;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_key (
    id integer NOT NULL,
    player_id integer NOT NULL,
    key_hash character varying(255) NOT NULL,
    key_prefix character varying(10) NOT NULL,
    name character varying(255),
    is_active boolean,
    last_used_at timestamp without time zone,
    created_at timestamp without time zone
);


--
-- Name: api_key_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_key_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_key_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_key_id_seq OWNED BY public.api_key.id;


--
-- Name: apikey; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.apikey (
    id integer NOT NULL,
    player_id integer NOT NULL,
    key_name character varying(100) NOT NULL,
    api_key character varying(255) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    last_used timestamp without time zone,
    expires_at timestamp without time zone
);


--
-- Name: apikey_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.apikey_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: apikey_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.apikey_id_seq OWNED BY public.apikey.id;


--
-- Name: dartboard; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dartboard (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    dartboard_id character varying(100) NOT NULL,
    wpa_key character varying(255) NOT NULL,
    name character varying(255),
    is_active boolean,
    last_connected timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: dartboard_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dartboard_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dartboard_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dartboard_id_seq OWNED BY public.dartboard.id;


--
-- Name: dartboard_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dartboard_type (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    brand character varying(100) NOT NULL,
    model character varying(100),
    description text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    master_pins text,
    slave_pins text
);


--
-- Name: dartboard_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dartboard_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dartboard_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dartboard_type_id_seq OWNED BY public.dartboard_type.id;


--
-- Name: dartboard_zone_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dartboard_zone_mapping (
    id integer NOT NULL,
    dartboard_type_id integer NOT NULL,
    master_pin integer NOT NULL,
    slave_pin integer NOT NULL,
    zone_number integer NOT NULL,
    multiplier_type character varying(20) NOT NULL,
    base_value integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: dartboard_zone_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dartboard_zone_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dartboard_zone_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dartboard_zone_mapping_id_seq OWNED BY public.dartboard_zone_mapping.id;


--
-- Name: gameresults; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gameresults (
    id integer NOT NULL,
    game_type_id integer NOT NULL,
    player_id integer NOT NULL,
    player_order integer NOT NULL,
    start_score integer,
    final_score integer,
    is_winner boolean,
    double_out_enabled boolean,
    started_at timestamp without time zone,
    finished_at timestamp without time zone,
    game_session_id character varying(100) NOT NULL,
    reset_on_miss boolean DEFAULT false NOT NULL
);


--
-- Name: gameresults_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.gameresults_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: gameresults_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.gameresults_id_seq OWNED BY public.gameresults.id;


--
-- Name: gametype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gametype (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    created_at timestamp without time zone
);


--
-- Name: gametype_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.gametype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: gametype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.gametype_id_seq OWNED BY public.gametype.id;


--
-- Name: hotspot_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hotspot_config (
    id integer NOT NULL,
    player_id integer NOT NULL,
    dartboard_id character varying(100) NOT NULL,
    wpa_key character varying(255) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: hotspot_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hotspot_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hotspot_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.hotspot_config_id_seq OWNED BY public.hotspot_config.id;


--
-- Name: player; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.player (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    created_at timestamp without time zone,
    username character varying(100),
    email character varying(255)
);


--
-- Name: player_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.player_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: player_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.player_id_seq OWNED BY public.player.id;


--
-- Name: scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scores (
    id integer NOT NULL,
    game_result_id integer NOT NULL,
    player_id integer NOT NULL,
    throw_sequence integer NOT NULL,
    turn_number integer NOT NULL,
    throw_in_turn integer NOT NULL,
    base_score integer NOT NULL,
    multiplier character varying(20) NOT NULL,
    multiplier_value integer NOT NULL,
    actual_score integer NOT NULL,
    score_before integer NOT NULL,
    score_after integer NOT NULL,
    dartboard_sends_actual_score boolean NOT NULL,
    is_bust boolean,
    is_finish boolean,
    thrown_at timestamp without time zone
);


--
-- Name: scores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scores_id_seq OWNED BY public.scores.id;


--
-- Name: training_score; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_score (
    id integer NOT NULL,
    training_session_id integer NOT NULL,
    player_id integer NOT NULL,
    throw_sequence integer NOT NULL,
    turn_number integer NOT NULL,
    throw_in_turn integer NOT NULL,
    base_score integer NOT NULL,
    multiplier character varying(20) NOT NULL,
    multiplier_value integer NOT NULL,
    actual_score integer NOT NULL,
    score_before integer NOT NULL,
    score_after integer NOT NULL,
    dartboard_sends_actual_score boolean NOT NULL,
    is_bust boolean,
    is_finish boolean,
    thrown_at timestamp without time zone
);


--
-- Name: training_score_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.training_score_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: training_score_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.training_score_id_seq OWNED BY public.training_score.id;


--
-- Name: training_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_session (
    id integer NOT NULL,
    player_id integer NOT NULL,
    game_type_id integer NOT NULL,
    session_id character varying(100) NOT NULL,
    start_score integer,
    final_score integer,
    double_out_enabled boolean,
    completed boolean,
    started_at timestamp without time zone,
    finished_at timestamp without time zone
);


--
-- Name: training_session_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.training_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: training_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.training_session_id_seq OWNED BY public.training_session.id;


--
-- Name: api_key id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key ALTER COLUMN id SET DEFAULT nextval('public.api_key_id_seq'::regclass);


--
-- Name: apikey id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apikey ALTER COLUMN id SET DEFAULT nextval('public.apikey_id_seq'::regclass);


--
-- Name: dartboard id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard ALTER COLUMN id SET DEFAULT nextval('public.dartboard_id_seq'::regclass);


--
-- Name: dartboard_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard_type ALTER COLUMN id SET DEFAULT nextval('public.dartboard_type_id_seq'::regclass);


--
-- Name: dartboard_zone_mapping id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard_zone_mapping ALTER COLUMN id SET DEFAULT nextval('public.dartboard_zone_mapping_id_seq'::regclass);


--
-- Name: gameresults id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gameresults ALTER COLUMN id SET DEFAULT nextval('public.gameresults_id_seq'::regclass);


--
-- Name: gametype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gametype ALTER COLUMN id SET DEFAULT nextval('public.gametype_id_seq'::regclass);


--
-- Name: hotspot_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hotspot_config ALTER COLUMN id SET DEFAULT nextval('public.hotspot_config_id_seq'::regclass);


--
-- Name: player id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player ALTER COLUMN id SET DEFAULT nextval('public.player_id_seq'::regclass);


--
-- Name: scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores ALTER COLUMN id SET DEFAULT nextval('public.scores_id_seq'::regclass);


--
-- Name: training_score id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_score ALTER COLUMN id SET DEFAULT nextval('public.training_score_id_seq'::regclass);


--
-- Name: training_session id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_session ALTER COLUMN id SET DEFAULT nextval('public.training_session_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
b2c3d4e5f6a7
\.


--
-- Data for Name: api_key; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.api_key (id, player_id, key_hash, key_prefix, name, is_active, last_used_at, created_at) FROM stdin;
\.


--
-- Data for Name: apikey; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.apikey (id, player_id, key_name, api_key, is_active, created_at, last_used, expires_at) FROM stdin;
\.


--
-- Data for Name: dartboard; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dartboard (id, owner_id, dartboard_id, wpa_key, name, is_active, last_connected, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dartboard_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dartboard_type (id, name, brand, model, description, is_active, created_at, updated_at, master_pins, slave_pins) FROM stdin;
1	winmau_ton_machine	Winmau	Ton Machine	Electronic dartboard	t	2026-05-18 12:16:20.202227	2026-05-18 12:16:20.202233	\N	\N
\.


--
-- Data for Name: dartboard_zone_mapping; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dartboard_zone_mapping (id, dartboard_type_id, master_pin, slave_pin, zone_number, multiplier_type, base_value, created_at, updated_at) FROM stdin;
1	1	16	33	17	SINGLE	17	2026-05-18 12:16:27.645658	2026-05-18 12:16:27.645662
2	1	4	33	17	DOUBLE	17	2026-05-18 12:16:27.706157	2026-05-18 12:16:27.706163
3	1	17	33	17	TRIPLE	17	2026-05-18 12:16:27.711248	2026-05-18 12:16:27.711253
4	1	4	32	3	DOUBLE	3	2026-05-18 12:16:27.716284	2026-05-18 12:16:27.716288
5	1	5	14	14	TRIPLE	14	2026-05-18 12:16:27.722047	2026-05-18 12:16:27.722051
6	1	16	32	3	SINGLE	3	2026-05-18 12:16:27.727325	2026-05-18 12:16:27.727329
7	1	17	32	3	TRIPLE	3	2026-05-18 12:16:27.732494	2026-05-18 12:16:27.732499
8	1	19	32	19	DOUBLE	19	2026-05-18 12:16:27.737793	2026-05-18 12:16:27.737797
9	1	18	32	19	SINGLE	19	2026-05-18 12:16:27.744126	2026-05-18 12:16:27.744131
10	1	5	32	19	TRIPLE	19	2026-05-18 12:16:27.74934	2026-05-18 12:16:27.749344
11	1	19	27	11	DOUBLE	11	2026-05-18 12:16:27.754408	2026-05-18 12:16:27.754412
12	1	18	27	11	SINGLE	11	2026-05-18 12:16:27.7595	2026-05-18 12:16:27.759505
13	1	5	27	11	TRIPLE	11	2026-05-18 12:16:27.764743	2026-05-18 12:16:27.764748
14	1	19	14	14	DOUBLE	14	2026-05-18 12:16:27.769576	2026-05-18 12:16:27.76958
15	1	18	14	14	SINGLE	14	2026-05-18 12:16:27.774266	2026-05-18 12:16:27.77427
16	1	19	12	9	DOUBLE	9	2026-05-18 12:16:27.779317	2026-05-18 12:16:27.779321
17	1	18	12	9	SINGLE	9	2026-05-18 12:16:27.784624	2026-05-18 12:16:27.784628
18	1	5	12	9	TRIPLE	9	2026-05-18 12:16:27.789719	2026-05-18 12:16:27.789723
19	1	19	13	12	DOUBLE	12	2026-05-18 12:16:27.794408	2026-05-18 12:16:27.794412
20	1	18	13	12	SINGLE	12	2026-05-18 12:16:27.799439	2026-05-18 12:16:27.799443
21	1	5	13	12	TRIPLE	12	2026-05-18 12:16:27.804657	2026-05-18 12:16:27.804662
22	1	2	27	5	TRIPLE	5	2026-05-18 12:16:27.812633	2026-05-18 12:16:27.812639
23	1	15	27	20	TRIPLE	20	2026-05-18 12:16:27.818493	2026-05-18 12:16:27.818498
24	1	15	33	1	DOUBLE	1	2026-05-18 12:16:27.824485	2026-05-18 12:16:27.824489
25	1	15	14	1	TRIPLE	1	2026-05-18 12:16:27.829623	2026-05-18 12:16:27.829628
26	1	15	12	25	DBLBULL	25	2026-05-18 12:16:27.834523	2026-05-18 12:16:27.834527
27	1	15	13	1	SINGLE	1	2026-05-18 12:16:27.839952	2026-05-18 12:16:27.839957
28	1	2	33	18	DOUBLE	18	2026-05-18 12:16:27.84458	2026-05-18 12:16:27.844585
29	1	2	13	18	SINGLE	18	2026-05-18 12:16:27.849625	2026-05-18 12:16:27.849631
30	1	2	14	18	TRIPLE	18	2026-05-18 12:16:27.854671	2026-05-18 12:16:27.854674
31	1	4	13	4	DOUBLE	4	2026-05-18 12:16:27.859492	2026-05-18 12:16:27.859498
32	1	16	13	4	SINGLE	4	2026-05-18 12:16:27.864789	2026-05-18 12:16:27.864793
33	1	17	13	4	TRIPLE	4	2026-05-18 12:16:27.869553	2026-05-18 12:16:27.869557
34	1	4	12	13	DOUBLE	13	2026-05-18 12:16:27.874813	2026-05-18 12:16:27.874818
35	1	16	12	13	SINGLE	13	2026-05-18 12:16:27.879823	2026-05-18 12:16:27.879827
36	1	17	12	13	TRIPLE	13	2026-05-18 12:16:27.884195	2026-05-18 12:16:27.884198
37	1	4	14	6	DOUBLE	6	2026-05-18 12:16:27.888619	2026-05-18 12:16:27.888623
38	1	16	14	6	SINGLE	6	2026-05-18 12:16:27.893065	2026-05-18 12:16:27.893069
39	1	17	14	6	TRIPLE	6	2026-05-18 12:16:27.897649	2026-05-18 12:16:27.897654
40	1	4	27	10	DOUBLE	10	2026-05-18 12:16:27.902254	2026-05-18 12:16:27.902259
41	1	16	27	10	SINGLE	10	2026-05-18 12:16:27.906648	2026-05-18 12:16:27.906651
42	1	17	27	10	TRIPLE	10	2026-05-18 12:16:27.911071	2026-05-18 12:16:27.911075
43	1	19	26	8	DOUBLE	8	2026-05-18 12:16:27.915439	2026-05-18 12:16:27.915443
44	1	18	26	8	SINGLE	8	2026-05-18 12:16:27.919992	2026-05-18 12:16:27.919996
45	1	15	25	20	DOUBLE	20	2026-05-18 12:16:27.925075	2026-05-18 12:16:27.925079
46	1	2	25	5	DOUBLE	5	2026-05-18 12:16:27.929044	2026-05-18 12:16:27.929047
47	1	4	25	2	DOUBLE	2	2026-05-18 12:16:27.933468	2026-05-18 12:16:27.933473
48	1	16	25	2	SINGLE	2	2026-05-18 12:16:27.937924	2026-05-18 12:16:27.937929
49	1	17	25	2	TRIPLE	2	2026-05-18 12:16:27.94344	2026-05-18 12:16:27.943444
50	1	18	33	7	SINGLE	7	2026-05-18 12:16:27.948893	2026-05-18 12:16:27.948897
51	1	19	33	7	DOUBLE	7	2026-05-18 12:16:27.953329	2026-05-18 12:16:27.953333
52	1	5	33	7	TRIPLE	7	2026-05-18 12:16:27.958084	2026-05-18 12:16:27.95809
53	1	19	25	16	DOUBLE	16	2026-05-18 12:16:27.962958	2026-05-18 12:16:27.962963
54	1	18	25	16	SINGLE	16	2026-05-18 12:16:27.967541	2026-05-18 12:16:27.967545
55	1	5	25	16	TRIPLE	16	2026-05-18 12:16:27.972025	2026-05-18 12:16:27.972029
56	1	15	26	20	SINGLE	20	2026-05-18 12:16:27.976773	2026-05-18 12:16:27.976777
57	1	2	26	5	SINGLE	5	2026-05-18 12:16:27.981197	2026-05-18 12:16:27.981201
58	1	4	26	15	DOUBLE	15	2026-05-18 12:16:27.986102	2026-05-18 12:16:27.986106
59	1	16	26	15	SINGLE	15	2026-05-18 12:16:27.99091	2026-05-18 12:16:27.990916
60	1	17	26	15	TRIPLE	15	2026-05-18 12:16:27.995643	2026-05-18 12:16:27.995647
61	1	5	26	8	TRIPLE	8	2026-05-18 12:16:28.000857	2026-05-18 12:16:28.000862
62	1	2	12	25	BULL	25	2026-05-18 12:16:28.005498	2026-05-18 12:16:28.005503
\.


--
-- Data for Name: gameresults; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.gameresults (id, game_type_id, player_id, player_order, start_score, final_score, is_winner, double_out_enabled, started_at, finished_at, game_session_id, reset_on_miss) FROM stdin;
1	1	1	0	301	301	f	f	2026-05-18 15:19:40.486386	\N	1e732ba4-7f06-41ff-80d2-8bbadb1a5e22	f
2	1	2	1	301	301	f	f	2026-05-18 15:19:40.521885	\N	1e732ba4-7f06-41ff-80d2-8bbadb1a5e22	f
3	4	1	0	\N	0	f	f	2026-05-18 15:19:40.576883	\N	2e0406ac-fe87-4d1d-b824-01c32acaac8f	f
4	4	2	1	\N	0	f	f	2026-05-18 15:19:40.58229	\N	2e0406ac-fe87-4d1d-b824-01c32acaac8f	f
5	3	1	0	501	501	f	f	2026-05-18 15:19:40.641506	\N	ae34fbda-41d3-4e2a-9c16-339b2afc1b14	f
6	3	2	1	501	501	f	f	2026-05-18 15:19:40.649812	\N	ae34fbda-41d3-4e2a-9c16-339b2afc1b14	f
7	1	1	0	301	301	f	f	2026-05-18 15:19:40.701736	\N	297b16cf-37d5-4c09-9e8b-390ac714124d	f
8	1	2	1	301	301	f	f	2026-05-18 15:19:40.706544	\N	297b16cf-37d5-4c09-9e8b-390ac714124d	f
9	1	1	0	301	301	f	f	2026-05-18 15:19:40.764319	\N	e6948f04-12e6-4142-8d9c-560844d60bbf	f
10	4	1	0	\N	0	f	f	2026-05-18 15:19:40.822432	\N	6630281f-5da5-40cf-8749-3587ac320702	f
11	4	2	1	\N	0	f	f	2026-05-18 15:19:40.827731	\N	6630281f-5da5-40cf-8749-3587ac320702	f
12	4	3	2	\N	0	f	f	2026-05-18 15:19:40.830707	\N	6630281f-5da5-40cf-8749-3587ac320702	f
13	4	4	3	\N	0	f	f	2026-05-18 15:19:40.833444	\N	6630281f-5da5-40cf-8749-3587ac320702	f
14	1	1	0	301	301	f	f	2026-05-18 15:19:40.887053	\N	074112dd-e0e0-4338-b4a0-fe03c5aba05a	f
15	1	2	1	301	301	f	f	2026-05-18 15:19:40.891564	\N	074112dd-e0e0-4338-b4a0-fe03c5aba05a	f
16	1	3	2	301	301	f	f	2026-05-18 15:19:40.894776	\N	074112dd-e0e0-4338-b4a0-fe03c5aba05a	f
17	1	1	0	301	301	f	f	2026-05-18 15:19:40.947269	\N	ac709aa0-7382-422a-b23d-22b641cd55ee	f
18	1	2	1	301	301	f	f	2026-05-18 15:19:40.952518	\N	ac709aa0-7382-422a-b23d-22b641cd55ee	f
19	1	1	0	301	301	f	f	2026-05-18 15:19:41.006636	\N	818ecb8f-9034-458c-98d7-ca45a2b1bc65	f
20	1	2	1	301	301	f	f	2026-05-18 15:19:41.012598	\N	818ecb8f-9034-458c-98d7-ca45a2b1bc65	f
21	1	1	0	301	301	f	f	2026-05-18 15:19:41.0772	\N	22be55d8-6d46-4f8f-87e7-5ee913a0cf6d	f
22	1	2	1	301	301	f	f	2026-05-18 15:19:41.081811	\N	22be55d8-6d46-4f8f-87e7-5ee913a0cf6d	f
23	1	1	0	301	301	f	f	2026-05-18 15:19:41.189352	\N	031d6be3-80e7-4a38-af5f-448fadbd7e39	f
24	1	2	1	301	301	f	f	2026-05-18 15:19:41.194259	\N	031d6be3-80e7-4a38-af5f-448fadbd7e39	f
25	1	1	0	301	301	f	f	2026-05-18 15:19:41.251976	\N	d88751f2-9ab0-4eac-b60a-b61bd71b419e	f
26	1	2	1	301	301	f	f	2026-05-18 15:19:41.256859	\N	d88751f2-9ab0-4eac-b60a-b61bd71b419e	f
27	1	1	0	301	301	f	f	2026-05-18 15:19:41.305759	\N	74a69db5-a46f-4e4b-9bb2-10cb95f9eaa9	f
28	1	2	1	301	301	f	f	2026-05-18 15:19:41.310551	\N	74a69db5-a46f-4e4b-9bb2-10cb95f9eaa9	f
29	1	1	0	301	301	f	f	2026-05-18 15:19:41.361349	\N	15a252a9-c845-4502-a310-39f3847f0638	f
30	1	2	1	301	301	f	f	2026-05-18 15:19:41.366416	\N	15a252a9-c845-4502-a310-39f3847f0638	f
31	1	3	2	301	301	f	f	2026-05-18 15:19:41.36881	\N	15a252a9-c845-4502-a310-39f3847f0638	f
32	1	1	0	301	301	f	f	2026-05-18 15:19:41.418188	\N	3726db4a-70bf-4357-8632-697148985885	f
33	1	2	1	301	301	f	f	2026-05-18 15:19:41.422824	\N	3726db4a-70bf-4357-8632-697148985885	f
34	1	1	0	301	301	f	f	2026-05-18 15:19:41.479415	\N	40890f91-439a-4f99-bf87-a47da98169df	f
35	1	2	1	301	301	f	f	2026-05-18 15:19:41.484237	\N	40890f91-439a-4f99-bf87-a47da98169df	f
36	1	1	0	301	301	f	f	2026-05-18 15:19:41.533475	\N	f11bb7de-724d-42f4-84a8-9bae7b9abf72	f
37	1	2	1	301	301	f	f	2026-05-18 15:19:41.537986	\N	f11bb7de-724d-42f4-84a8-9bae7b9abf72	f
38	1	1	0	301	301	f	f	2026-05-18 15:19:41.588417	\N	62e2880a-8196-49c9-b65f-ec74d9968be0	f
39	1	2	1	301	301	f	f	2026-05-18 15:19:41.593332	\N	62e2880a-8196-49c9-b65f-ec74d9968be0	f
41	1	2	1	301	301	f	f	2026-05-18 15:19:41.932275	\N	4a246b5e-41c9-47fc-86d3-40742ae30290	f
40	1	1	0	301	241	f	f	2026-05-18 15:19:41.927152	\N	4a246b5e-41c9-47fc-86d3-40742ae30290	f
42	1	1	0	301	301	f	f	2026-05-18 15:19:42.008529	\N	9c53471e-ccfb-47d3-ac41-f85d8ae58da3	f
43	1	2	1	301	301	f	f	2026-05-18 15:19:42.013246	\N	9c53471e-ccfb-47d3-ac41-f85d8ae58da3	f
44	1	1	0	301	301	t	f	2026-05-18 15:19:42.072582	2026-05-18 15:19:42.094858	a08bd254-218d-44d1-8ef3-9c9380c9de2e	f
45	1	2	1	301	301	f	f	2026-05-18 15:19:42.082131	2026-05-18 15:19:42.099169	a08bd254-218d-44d1-8ef3-9c9380c9de2e	f
46	1	1	0	301	301	t	f	2026-05-18 15:19:42.14942	2026-05-18 15:19:42.166804	3335db7b-d411-442d-9c96-e8f8850f206c	f
47	1	2	1	301	301	f	f	2026-05-18 15:19:42.154418	2026-05-18 15:19:42.171339	3335db7b-d411-442d-9c96-e8f8850f206c	f
48	1	1	0	301	301	f	f	2026-05-18 15:19:42.269205	\N	7e2f0852-e826-4892-b764-ca1b9f5eb53d	f
49	1	2	1	301	301	f	f	2026-05-18 15:19:42.274333	\N	7e2f0852-e826-4892-b764-ca1b9f5eb53d	f
50	1	1	0	301	301	f	f	2026-05-18 15:19:42.327873	\N	fc4594ab-d739-41d2-ab53-f9c3d7341e94	f
51	1	2	1	301	301	f	f	2026-05-18 15:19:42.332954	\N	fc4594ab-d739-41d2-ab53-f9c3d7341e94	f
52	1	1	0	301	301	f	f	2026-05-18 15:19:42.399279	\N	c586b26b-1af0-4925-90da-864f249137c8	f
53	1	2	1	301	301	f	f	2026-05-18 15:19:42.403932	\N	c586b26b-1af0-4925-90da-864f249137c8	f
54	1	1	0	301	301	f	f	2026-05-18 15:19:42.46751	\N	48496dea-679a-4877-a23d-0c61584259e6	f
55	1	2	1	301	301	f	f	2026-05-18 15:19:42.472884	\N	48496dea-679a-4877-a23d-0c61584259e6	f
56	4	1	0	\N	0	f	f	2026-05-18 15:19:42.550828	\N	1add7acb-20a6-423f-a91b-598a1ebf7e9f	f
57	4	2	1	\N	0	f	f	2026-05-18 15:19:42.555643	\N	1add7acb-20a6-423f-a91b-598a1ebf7e9f	f
58	1	1	0	301	301	f	f	2026-05-18 15:19:42.617934	\N	2482da37-3bae-44ce-8ae2-bb6719b2914f	f
59	1	2	1	301	301	f	f	2026-05-18 15:19:42.622724	\N	2482da37-3bae-44ce-8ae2-bb6719b2914f	f
60	4	1	0	\N	0	f	f	2026-05-18 15:19:42.67548	\N	711d6d78-370d-4112-a16c-17439b13df9c	f
61	4	2	1	\N	0	f	f	2026-05-18 15:19:42.681286	\N	711d6d78-370d-4112-a16c-17439b13df9c	f
62	1	1	0	301	301	f	f	2026-05-18 15:19:42.740074	\N	6ef6563b-3ac0-4559-a5ed-7cc4d7c24556	f
63	1	2	1	301	301	f	f	2026-05-18 15:19:42.746451	\N	6ef6563b-3ac0-4559-a5ed-7cc4d7c24556	f
65	1	2	1	301	301	f	f	2026-05-18 15:19:42.840549	\N	8b4d49ec-daef-461c-848d-0f7929185ff7	f
64	1	1	0	301	281	f	f	2026-05-18 15:19:42.83423	\N	8b4d49ec-daef-461c-848d-0f7929185ff7	f
66	1	1	0	301	301	f	f	2026-05-18 15:19:42.925363	\N	44ec03a8-e92d-4f9d-a45b-c485789ba751	f
67	1	2	1	301	301	f	f	2026-05-18 15:19:42.931216	\N	44ec03a8-e92d-4f9d-a45b-c485789ba751	f
69	1	2	1	301	301	f	f	2026-05-18 15:19:43.005192	\N	704ed4d4-a693-4b64-a59f-5924c50b9ca1	f
68	1	1	0	301	251	f	f	2026-05-18 15:19:42.99928	\N	704ed4d4-a693-4b64-a59f-5924c50b9ca1	f
70	1	1	0	301	301	f	f	2026-05-18 15:19:43.135265	\N	e1f0e31c-7861-4980-9625-2b156b5f0697	f
71	1	2	1	301	301	f	f	2026-05-18 15:19:43.14279	\N	e1f0e31c-7861-4980-9625-2b156b5f0697	f
\.


--
-- Data for Name: gametype; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.gametype (id, name, description, created_at) FROM stdin;
1	301	301 darts game	2026-03-02 20:18:10.288746
2	401	401 darts game	2026-03-02 20:18:10.290348
3	501	501 darts game	2026-03-02 20:18:10.291547
4	cricket	Cricket darts game	2026-03-02 20:18:10.2926
5	round_the_clock	Round the Clock                     - hit numbers 1-20 in order                     - hit single and double bull to win	2026-03-02 20:18:10.293579
6	round_the_clock_double	Round the Clock Double                     - hit numbers 1-20 in order                     - hit double bull to win	2026-03-02 20:18:10.294819
7	bull_practice	Bull Practice                     - training game to practice hitting bulls                     - auto-restarts after each round	2026-03-02 20:18:10.295901
\.


--
-- Data for Name: hotspot_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hotspot_config (id, player_id, dartboard_id, wpa_key, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: player; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.player (id, name, created_at, username, email) FROM stdin;
1	Bypass User	2026-03-02 20:22:32.735284	bypass_user	bypass@local.dev
2	admin	2026-03-02 20:44:55.9714	admin	\N
3	Dennis User	2026-03-02 20:46:03.07542	Dennis	Dennis@letsplaydarts.eu
4	TestPlayer	2026-05-15 07:39:06.169524	testplayer	test@example.com
5	John Doe	2026-05-19 08:56:05.35439	john_doe	john@example.com
\.


--
-- Data for Name: scores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scores (id, game_result_id, player_id, throw_sequence, turn_number, throw_in_turn, base_score, multiplier, multiplier_value, actual_score, score_before, score_after, dartboard_sends_actual_score, is_bust, is_finish, thrown_at) FROM stdin;
1	19	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:41.021736
2	21	1	1	1	1	20	TRIPLE	3	60	301	241	f	f	f	2026-05-18 15:19:41.088089
3	40	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:41.938919
4	40	1	2	1	2	20	SINGLE	1	20	281	261	f	f	f	2026-05-18 15:19:41.945526
5	40	1	3	1	3	20	SINGLE	1	20	261	241	f	f	f	2026-05-18 15:19:41.949761
6	42	1	1	1	1	20	SINGLE	1	20	10	10	f	t	f	2026-05-18 15:19:42.019691
7	44	1	1	1	1	20	SINGLE	1	20	20	0	f	f	t	2026-05-18 15:19:42.088908
8	46	1	1	1	1	20	SINGLE	1	20	20	0	f	f	t	2026-05-18 15:19:42.160961
9	50	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:42.339505
10	50	1	2	1	2	7	DOUBLE	2	14	281	267	f	f	f	2026-05-18 15:19:42.346867
11	52	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:42.410163
12	54	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:42.479433
15	56	1	1	1	1	20	TRIPLE	3	60	0	0	f	f	f	2026-05-18 15:19:42.561906
16	62	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:42.758699
19	64	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:42.84938
20	64	1	2	1	2	0	SINGLE	1	0	281	281	f	f	f	2026-05-18 15:19:42.857699
21	64	1	3	1	3	0	SINGLE	1	0	281	281	f	f	f	2026-05-18 15:19:42.861323
22	66	1	1	1	1	0	SINGLE	1	0	301	301	f	f	f	2026-05-18 15:19:42.938137
23	66	1	2	1	2	0	SINGLE	1	0	301	301	f	f	f	2026-05-18 15:19:42.94437
24	66	1	3	1	3	0	SINGLE	1	0	301	301	f	f	f	2026-05-18 15:19:42.948327
25	68	1	1	1	1	20	SINGLE	1	20	301	281	f	f	f	2026-05-18 15:19:43.012637
26	68	1	2	1	2	15	DOUBLE	2	30	281	251	f	f	f	2026-05-18 15:19:43.019671
27	68	1	3	1	3	0	SINGLE	1	0	251	251	f	f	f	2026-05-18 15:19:43.02477
\.


--
-- Data for Name: training_score; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.training_score (id, training_session_id, player_id, throw_sequence, turn_number, throw_in_turn, base_score, multiplier, multiplier_value, actual_score, score_before, score_after, dartboard_sends_actual_score, is_bust, is_finish, thrown_at) FROM stdin;
\.


--
-- Data for Name: training_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.training_session (id, player_id, game_type_id, session_id, start_score, final_score, double_out_enabled, completed, started_at, finished_at) FROM stdin;
\.


--
-- Name: api_key_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.api_key_id_seq', 1, false);


--
-- Name: apikey_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.apikey_id_seq', 1, false);


--
-- Name: dartboard_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dartboard_id_seq', 1, false);


--
-- Name: dartboard_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dartboard_type_id_seq', 1, true);


--
-- Name: dartboard_zone_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dartboard_zone_mapping_id_seq', 62, true);


--
-- Name: gameresults_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.gameresults_id_seq', 71, true);


--
-- Name: gametype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.gametype_id_seq', 7, true);


--
-- Name: hotspot_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hotspot_config_id_seq', 1, false);


--
-- Name: player_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.player_id_seq', 5, true);


--
-- Name: scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scores_id_seq', 27, true);


--
-- Name: training_score_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.training_score_id_seq', 1, false);


--
-- Name: training_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.training_session_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_key api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_pkey PRIMARY KEY (id);


--
-- Name: apikey apikey_api_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apikey
    ADD CONSTRAINT apikey_api_key_key UNIQUE (api_key);


--
-- Name: apikey apikey_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apikey
    ADD CONSTRAINT apikey_pkey PRIMARY KEY (id);


--
-- Name: dartboard dartboard_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard
    ADD CONSTRAINT dartboard_pkey PRIMARY KEY (id);


--
-- Name: dartboard_type dartboard_type_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard_type
    ADD CONSTRAINT dartboard_type_name_key UNIQUE (name);


--
-- Name: dartboard_type dartboard_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard_type
    ADD CONSTRAINT dartboard_type_pkey PRIMARY KEY (id);


--
-- Name: dartboard_zone_mapping dartboard_zone_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard_zone_mapping
    ADD CONSTRAINT dartboard_zone_mapping_pkey PRIMARY KEY (id);


--
-- Name: gameresults gameresults_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gameresults
    ADD CONSTRAINT gameresults_pkey PRIMARY KEY (id);


--
-- Name: gametype gametype_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gametype
    ADD CONSTRAINT gametype_name_key UNIQUE (name);


--
-- Name: gametype gametype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gametype
    ADD CONSTRAINT gametype_pkey PRIMARY KEY (id);


--
-- Name: hotspot_config hotspot_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hotspot_config
    ADD CONSTRAINT hotspot_config_pkey PRIMARY KEY (id);


--
-- Name: player player_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player
    ADD CONSTRAINT player_pkey PRIMARY KEY (id);


--
-- Name: scores scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_pkey PRIMARY KEY (id);


--
-- Name: training_score training_score_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_score
    ADD CONSTRAINT training_score_pkey PRIMARY KEY (id);


--
-- Name: training_session training_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_session
    ADD CONSTRAINT training_session_pkey PRIMARY KEY (id);


--
-- Name: training_session training_session_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_session
    ADD CONSTRAINT training_session_session_id_key UNIQUE (session_id);


--
-- Name: ix_api_key_key_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_api_key_key_hash ON public.api_key USING btree (key_hash);


--
-- Name: ix_dartboard_dartboard_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_dartboard_dartboard_id ON public.dartboard USING btree (dartboard_id);


--
-- Name: ix_dartboard_zone_mapping_dartboard_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dartboard_zone_mapping_dartboard_type_id ON public.dartboard_zone_mapping USING btree (dartboard_type_id);


--
-- Name: ix_player_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_player_email ON public.player USING btree (email);


--
-- Name: ix_player_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_player_username ON public.player USING btree (username);


--
-- Name: api_key api_key_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- Name: apikey apikey_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apikey
    ADD CONSTRAINT apikey_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- Name: dartboard dartboard_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard
    ADD CONSTRAINT dartboard_player_id_fkey FOREIGN KEY (owner_id) REFERENCES public.player(id);


--
-- Name: dartboard_zone_mapping dartboard_zone_mapping_dartboard_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dartboard_zone_mapping
    ADD CONSTRAINT dartboard_zone_mapping_dartboard_type_id_fkey FOREIGN KEY (dartboard_type_id) REFERENCES public.dartboard_type(id);


--
-- Name: gameresults gameresults_game_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gameresults
    ADD CONSTRAINT gameresults_game_type_id_fkey FOREIGN KEY (game_type_id) REFERENCES public.gametype(id);


--
-- Name: gameresults gameresults_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gameresults
    ADD CONSTRAINT gameresults_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- Name: hotspot_config hotspot_config_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hotspot_config
    ADD CONSTRAINT hotspot_config_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- Name: scores scores_game_result_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_game_result_id_fkey FOREIGN KEY (game_result_id) REFERENCES public.gameresults(id);


--
-- Name: scores scores_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- Name: training_score training_score_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_score
    ADD CONSTRAINT training_score_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- Name: training_score training_score_training_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_score
    ADD CONSTRAINT training_score_training_session_id_fkey FOREIGN KEY (training_session_id) REFERENCES public.training_session(id);


--
-- Name: training_session training_session_game_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_session
    ADD CONSTRAINT training_session_game_type_id_fkey FOREIGN KEY (game_type_id) REFERENCES public.gametype(id);


--
-- Name: training_session training_session_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_session
    ADD CONSTRAINT training_session_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(id);


--
-- PostgreSQL database dump complete
--

\unrestrict bcThKSGb4CZigPvoTYKu46GdmxyfZDqjOWaHcsdpW3ZHR36JOIgxMcWbHCI641I

