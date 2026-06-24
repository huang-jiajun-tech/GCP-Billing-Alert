--
-- PostgreSQL database dump
--

\restrict 3Mmhdo0zLSF8kg4mgpncRbxFmthhw1mdld2e31f8dohBNBd5N9Xsfhi2ZuKQvWd

-- Dumped from database version 16.12 (Debian 16.12-1.pgdg13+1)
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alert_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alert_configs (
    id integer NOT NULL,
    alert_name character varying NOT NULL,
    project_ids jsonb,
    threshold double precision NOT NULL,
    email character varying,
    webhook_url character varying,
    is_active boolean,
    time_range_days integer DEFAULT 1,
    service_description character varying(255)
);


ALTER TABLE public.alert_configs OWNER TO postgres;

--
-- Name: alert_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alert_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_configs_id_seq OWNER TO postgres;

--
-- Name: alert_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alert_configs_id_seq OWNED BY public.alert_configs.id;


--
-- Name: alert_incidents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alert_incidents (
    id integer NOT NULL,
    alert_config_id integer NOT NULL,
    project_id character varying NOT NULL,
    cost double precision NOT NULL,
    threshold double precision NOT NULL,
    usage_date character varying NOT NULL,
    status character varying,
    created_at timestamp without time zone,
    handled_at timestamp without time zone,
    handler_id integer,
    handle_notes character varying
);


ALTER TABLE public.alert_incidents OWNER TO postgres;

--
-- Name: alert_incidents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alert_incidents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_incidents_id_seq OWNER TO postgres;

--
-- Name: alert_incidents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alert_incidents_id_seq OWNED BY public.alert_incidents.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action character varying NOT NULL,
    details character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: billing_accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.billing_accounts (
    id integer NOT NULL,
    billing_account_id character varying NOT NULL,
    display_name character varying NOT NULL,
    last_updated timestamp without time zone
);


ALTER TABLE public.billing_accounts OWNER TO postgres;

--
-- Name: billing_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.billing_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.billing_accounts_id_seq OWNER TO postgres;

--
-- Name: billing_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.billing_accounts_id_seq OWNED BY public.billing_accounts.id;


--
-- Name: daily_usage; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage (
    id integer NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
)
PARTITION BY RANGE (usage_date);


ALTER TABLE public.daily_usage OWNER TO postgres;

--
-- Name: daily_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.daily_usage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.daily_usage_id_seq OWNER TO postgres;

--
-- Name: daily_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.daily_usage_id_seq OWNED BY public.daily_usage.id;


--
-- Name: daily_usage_2024_01; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_01 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_01 OWNER TO postgres;

--
-- Name: daily_usage_2024_02; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_02 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_02 OWNER TO postgres;

--
-- Name: daily_usage_2024_03; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_03 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_03 OWNER TO postgres;

--
-- Name: daily_usage_2024_04; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_04 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_04 OWNER TO postgres;

--
-- Name: daily_usage_2024_05; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_05 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_05 OWNER TO postgres;

--
-- Name: daily_usage_2024_06; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_06 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_06 OWNER TO postgres;

--
-- Name: daily_usage_2024_07; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_07 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_07 OWNER TO postgres;

--
-- Name: daily_usage_2024_08; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_08 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_08 OWNER TO postgres;

--
-- Name: daily_usage_2024_09; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_09 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_09 OWNER TO postgres;

--
-- Name: daily_usage_2024_10; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_10 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_10 OWNER TO postgres;

--
-- Name: daily_usage_2024_11; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_11 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_11 OWNER TO postgres;

--
-- Name: daily_usage_2024_12; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2024_12 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2024_12 OWNER TO postgres;

--
-- Name: daily_usage_2025_01; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_01 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_01 OWNER TO postgres;

--
-- Name: daily_usage_2025_02; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_02 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_02 OWNER TO postgres;

--
-- Name: daily_usage_2025_03; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_03 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_03 OWNER TO postgres;

--
-- Name: daily_usage_2025_04; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_04 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_04 OWNER TO postgres;

--
-- Name: daily_usage_2025_05; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_05 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_05 OWNER TO postgres;

--
-- Name: daily_usage_2025_06; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_06 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_06 OWNER TO postgres;

--
-- Name: daily_usage_2025_07; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_07 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_07 OWNER TO postgres;

--
-- Name: daily_usage_2025_08; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_08 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_08 OWNER TO postgres;

--
-- Name: daily_usage_2025_09; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_09 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_09 OWNER TO postgres;

--
-- Name: daily_usage_2025_10; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_10 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_10 OWNER TO postgres;

--
-- Name: daily_usage_2025_11; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_11 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_11 OWNER TO postgres;

--
-- Name: daily_usage_2025_12; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2025_12 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2025_12 OWNER TO postgres;

--
-- Name: daily_usage_2026_01; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_01 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_01 OWNER TO postgres;

--
-- Name: daily_usage_2026_02; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_02 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_02 OWNER TO postgres;

--
-- Name: daily_usage_2026_03; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_03 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_03 OWNER TO postgres;

--
-- Name: daily_usage_2026_04; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_04 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_04 OWNER TO postgres;

--
-- Name: daily_usage_2026_05; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_05 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_05 OWNER TO postgres;

--
-- Name: daily_usage_2026_06; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_06 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_06 OWNER TO postgres;

--
-- Name: daily_usage_2026_07; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_07 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_07 OWNER TO postgres;

--
-- Name: daily_usage_2026_08; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_08 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_08 OWNER TO postgres;

--
-- Name: daily_usage_2026_09; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_09 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_09 OWNER TO postgres;

--
-- Name: daily_usage_2026_10; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_10 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_10 OWNER TO postgres;

--
-- Name: daily_usage_2026_11; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_11 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_11 OWNER TO postgres;

--
-- Name: daily_usage_2026_12; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2026_12 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2026_12 OWNER TO postgres;

--
-- Name: daily_usage_2027_01; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_01 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_01 OWNER TO postgres;

--
-- Name: daily_usage_2027_02; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_02 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_02 OWNER TO postgres;

--
-- Name: daily_usage_2027_03; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_03 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_03 OWNER TO postgres;

--
-- Name: daily_usage_2027_04; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_04 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_04 OWNER TO postgres;

--
-- Name: daily_usage_2027_05; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_05 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_05 OWNER TO postgres;

--
-- Name: daily_usage_2027_06; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_06 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_06 OWNER TO postgres;

--
-- Name: daily_usage_2027_07; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_07 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_07 OWNER TO postgres;

--
-- Name: daily_usage_2027_08; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_08 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_08 OWNER TO postgres;

--
-- Name: daily_usage_2027_09; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_09 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_09 OWNER TO postgres;

--
-- Name: daily_usage_2027_10; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_10 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_10 OWNER TO postgres;

--
-- Name: daily_usage_2027_11; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_11 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_11 OWNER TO postgres;

--
-- Name: daily_usage_2027_12; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_usage_2027_12 (
    id integer DEFAULT nextval('public.daily_usage_id_seq'::regclass) NOT NULL,
    project_id character varying NOT NULL,
    billing_account_id character varying,
    service_description character varying,
    usage_date date NOT NULL,
    cost double precision NOT NULL,
    currency character varying DEFAULT 'USD'::character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.daily_usage_2027_12 OWNER TO postgres;

--
-- Name: project_info; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_info (
    project_id text,
    customer_name text,
    sales_rep text
);


ALTER TABLE public.project_info OWNER TO postgres;

--
-- Name: sync_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sync_logs (
    id integer NOT NULL,
    sync_type character varying NOT NULL,
    target_start_date date NOT NULL,
    target_end_date date NOT NULL,
    status character varying NOT NULL,
    records_synced integer,
    error_message character varying,
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);


ALTER TABLE public.sync_logs OWNER TO postgres;

--
-- Name: sync_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sync_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_logs_id_seq OWNER TO postgres;

--
-- Name: sync_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sync_logs_id_seq OWNED BY public.sync_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    role character varying,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: daily_usage_2024_01; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_01 FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');


--
-- Name: daily_usage_2024_02; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_02 FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');


--
-- Name: daily_usage_2024_03; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_03 FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');


--
-- Name: daily_usage_2024_04; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_04 FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');


--
-- Name: daily_usage_2024_05; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_05 FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');


--
-- Name: daily_usage_2024_06; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_06 FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');


--
-- Name: daily_usage_2024_07; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_07 FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');


--
-- Name: daily_usage_2024_08; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_08 FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');


--
-- Name: daily_usage_2024_09; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_09 FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');


--
-- Name: daily_usage_2024_10; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_10 FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');


--
-- Name: daily_usage_2024_11; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_11 FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');


--
-- Name: daily_usage_2024_12; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2024_12 FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');


--
-- Name: daily_usage_2025_01; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_01 FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');


--
-- Name: daily_usage_2025_02; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_02 FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');


--
-- Name: daily_usage_2025_03; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_03 FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');


--
-- Name: daily_usage_2025_04; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_04 FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');


--
-- Name: daily_usage_2025_05; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_05 FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');


--
-- Name: daily_usage_2025_06; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_06 FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');


--
-- Name: daily_usage_2025_07; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_07 FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');


--
-- Name: daily_usage_2025_08; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_08 FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');


--
-- Name: daily_usage_2025_09; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_09 FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');


--
-- Name: daily_usage_2025_10; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_10 FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');


--
-- Name: daily_usage_2025_11; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_11 FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');


--
-- Name: daily_usage_2025_12; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2025_12 FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');


--
-- Name: daily_usage_2026_01; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_01 FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');


--
-- Name: daily_usage_2026_02; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_02 FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');


--
-- Name: daily_usage_2026_03; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_03 FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');


--
-- Name: daily_usage_2026_04; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_04 FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');


--
-- Name: daily_usage_2026_05; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_05 FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');


--
-- Name: daily_usage_2026_06; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_06 FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');


--
-- Name: daily_usage_2026_07; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_07 FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');


--
-- Name: daily_usage_2026_08; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_08 FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');


--
-- Name: daily_usage_2026_09; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_09 FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');


--
-- Name: daily_usage_2026_10; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_10 FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');


--
-- Name: daily_usage_2026_11; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_11 FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');


--
-- Name: daily_usage_2026_12; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2026_12 FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');


--
-- Name: daily_usage_2027_01; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_01 FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');


--
-- Name: daily_usage_2027_02; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_02 FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');


--
-- Name: daily_usage_2027_03; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_03 FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');


--
-- Name: daily_usage_2027_04; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_04 FOR VALUES FROM ('2027-04-01') TO ('2027-05-01');


--
-- Name: daily_usage_2027_05; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_05 FOR VALUES FROM ('2027-05-01') TO ('2027-06-01');


--
-- Name: daily_usage_2027_06; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_06 FOR VALUES FROM ('2027-06-01') TO ('2027-07-01');


--
-- Name: daily_usage_2027_07; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_07 FOR VALUES FROM ('2027-07-01') TO ('2027-08-01');


--
-- Name: daily_usage_2027_08; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_08 FOR VALUES FROM ('2027-08-01') TO ('2027-09-01');


--
-- Name: daily_usage_2027_09; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_09 FOR VALUES FROM ('2027-09-01') TO ('2027-10-01');


--
-- Name: daily_usage_2027_10; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_10 FOR VALUES FROM ('2027-10-01') TO ('2027-11-01');


--
-- Name: daily_usage_2027_11; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_11 FOR VALUES FROM ('2027-11-01') TO ('2027-12-01');


--
-- Name: daily_usage_2027_12; Type: TABLE ATTACH; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ATTACH PARTITION public.daily_usage_2027_12 FOR VALUES FROM ('2027-12-01') TO ('2028-01-01');


--
-- Name: alert_configs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert_configs ALTER COLUMN id SET DEFAULT nextval('public.alert_configs_id_seq'::regclass);


--
-- Name: alert_incidents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert_incidents ALTER COLUMN id SET DEFAULT nextval('public.alert_incidents_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: billing_accounts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_accounts ALTER COLUMN id SET DEFAULT nextval('public.billing_accounts_id_seq'::regclass);


--
-- Name: daily_usage id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage ALTER COLUMN id SET DEFAULT nextval('public.daily_usage_id_seq'::regclass);


--
-- Name: sync_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_logs ALTER COLUMN id SET DEFAULT nextval('public.sync_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alert_configs alert_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert_configs
    ADD CONSTRAINT alert_configs_pkey PRIMARY KEY (id);


--
-- Name: alert_incidents alert_incidents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert_incidents
    ADD CONSTRAINT alert_incidents_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: billing_accounts billing_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_accounts
    ADD CONSTRAINT billing_accounts_pkey PRIMARY KEY (id);


--
-- Name: daily_usage daily_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage
    ADD CONSTRAINT daily_usage_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_01 daily_usage_2024_01_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_01
    ADD CONSTRAINT daily_usage_2024_01_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage uix_daily_usage; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage
    ADD CONSTRAINT uix_daily_usage UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_01 daily_usage_2024_01_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_01
    ADD CONSTRAINT daily_usage_2024_01_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_02 daily_usage_2024_02_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_02
    ADD CONSTRAINT daily_usage_2024_02_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_02 daily_usage_2024_02_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_02
    ADD CONSTRAINT daily_usage_2024_02_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_03 daily_usage_2024_03_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_03
    ADD CONSTRAINT daily_usage_2024_03_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_03 daily_usage_2024_03_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_03
    ADD CONSTRAINT daily_usage_2024_03_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_04 daily_usage_2024_04_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_04
    ADD CONSTRAINT daily_usage_2024_04_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_04 daily_usage_2024_04_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_04
    ADD CONSTRAINT daily_usage_2024_04_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_05 daily_usage_2024_05_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_05
    ADD CONSTRAINT daily_usage_2024_05_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_05 daily_usage_2024_05_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_05
    ADD CONSTRAINT daily_usage_2024_05_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_06 daily_usage_2024_06_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_06
    ADD CONSTRAINT daily_usage_2024_06_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_06 daily_usage_2024_06_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_06
    ADD CONSTRAINT daily_usage_2024_06_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_07 daily_usage_2024_07_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_07
    ADD CONSTRAINT daily_usage_2024_07_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_07 daily_usage_2024_07_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_07
    ADD CONSTRAINT daily_usage_2024_07_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_08 daily_usage_2024_08_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_08
    ADD CONSTRAINT daily_usage_2024_08_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_08 daily_usage_2024_08_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_08
    ADD CONSTRAINT daily_usage_2024_08_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_09 daily_usage_2024_09_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_09
    ADD CONSTRAINT daily_usage_2024_09_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_09 daily_usage_2024_09_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_09
    ADD CONSTRAINT daily_usage_2024_09_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_10 daily_usage_2024_10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_10
    ADD CONSTRAINT daily_usage_2024_10_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_10 daily_usage_2024_10_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_10
    ADD CONSTRAINT daily_usage_2024_10_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_11 daily_usage_2024_11_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_11
    ADD CONSTRAINT daily_usage_2024_11_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_11 daily_usage_2024_11_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_11
    ADD CONSTRAINT daily_usage_2024_11_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2024_12 daily_usage_2024_12_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_12
    ADD CONSTRAINT daily_usage_2024_12_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2024_12 daily_usage_2024_12_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2024_12
    ADD CONSTRAINT daily_usage_2024_12_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_01 daily_usage_2025_01_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_01
    ADD CONSTRAINT daily_usage_2025_01_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_01 daily_usage_2025_01_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_01
    ADD CONSTRAINT daily_usage_2025_01_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_02 daily_usage_2025_02_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_02
    ADD CONSTRAINT daily_usage_2025_02_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_02 daily_usage_2025_02_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_02
    ADD CONSTRAINT daily_usage_2025_02_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_03 daily_usage_2025_03_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_03
    ADD CONSTRAINT daily_usage_2025_03_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_03 daily_usage_2025_03_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_03
    ADD CONSTRAINT daily_usage_2025_03_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_04 daily_usage_2025_04_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_04
    ADD CONSTRAINT daily_usage_2025_04_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_04 daily_usage_2025_04_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_04
    ADD CONSTRAINT daily_usage_2025_04_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_05 daily_usage_2025_05_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_05
    ADD CONSTRAINT daily_usage_2025_05_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_05 daily_usage_2025_05_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_05
    ADD CONSTRAINT daily_usage_2025_05_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_06 daily_usage_2025_06_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_06
    ADD CONSTRAINT daily_usage_2025_06_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_06 daily_usage_2025_06_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_06
    ADD CONSTRAINT daily_usage_2025_06_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_07 daily_usage_2025_07_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_07
    ADD CONSTRAINT daily_usage_2025_07_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_07 daily_usage_2025_07_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_07
    ADD CONSTRAINT daily_usage_2025_07_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_08 daily_usage_2025_08_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_08
    ADD CONSTRAINT daily_usage_2025_08_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_08 daily_usage_2025_08_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_08
    ADD CONSTRAINT daily_usage_2025_08_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_09 daily_usage_2025_09_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_09
    ADD CONSTRAINT daily_usage_2025_09_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_09 daily_usage_2025_09_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_09
    ADD CONSTRAINT daily_usage_2025_09_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_10 daily_usage_2025_10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_10
    ADD CONSTRAINT daily_usage_2025_10_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_10 daily_usage_2025_10_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_10
    ADD CONSTRAINT daily_usage_2025_10_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_11 daily_usage_2025_11_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_11
    ADD CONSTRAINT daily_usage_2025_11_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_11 daily_usage_2025_11_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_11
    ADD CONSTRAINT daily_usage_2025_11_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2025_12 daily_usage_2025_12_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_12
    ADD CONSTRAINT daily_usage_2025_12_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2025_12 daily_usage_2025_12_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2025_12
    ADD CONSTRAINT daily_usage_2025_12_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_01 daily_usage_2026_01_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_01
    ADD CONSTRAINT daily_usage_2026_01_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_01 daily_usage_2026_01_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_01
    ADD CONSTRAINT daily_usage_2026_01_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_02 daily_usage_2026_02_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_02
    ADD CONSTRAINT daily_usage_2026_02_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_02 daily_usage_2026_02_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_02
    ADD CONSTRAINT daily_usage_2026_02_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_03 daily_usage_2026_03_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_03
    ADD CONSTRAINT daily_usage_2026_03_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_03 daily_usage_2026_03_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_03
    ADD CONSTRAINT daily_usage_2026_03_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_04 daily_usage_2026_04_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_04
    ADD CONSTRAINT daily_usage_2026_04_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_04 daily_usage_2026_04_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_04
    ADD CONSTRAINT daily_usage_2026_04_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_05 daily_usage_2026_05_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_05
    ADD CONSTRAINT daily_usage_2026_05_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_05 daily_usage_2026_05_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_05
    ADD CONSTRAINT daily_usage_2026_05_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_06 daily_usage_2026_06_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_06
    ADD CONSTRAINT daily_usage_2026_06_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_06 daily_usage_2026_06_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_06
    ADD CONSTRAINT daily_usage_2026_06_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_07 daily_usage_2026_07_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_07
    ADD CONSTRAINT daily_usage_2026_07_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_07 daily_usage_2026_07_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_07
    ADD CONSTRAINT daily_usage_2026_07_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_08 daily_usage_2026_08_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_08
    ADD CONSTRAINT daily_usage_2026_08_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_08 daily_usage_2026_08_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_08
    ADD CONSTRAINT daily_usage_2026_08_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_09 daily_usage_2026_09_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_09
    ADD CONSTRAINT daily_usage_2026_09_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_09 daily_usage_2026_09_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_09
    ADD CONSTRAINT daily_usage_2026_09_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_10 daily_usage_2026_10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_10
    ADD CONSTRAINT daily_usage_2026_10_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_10 daily_usage_2026_10_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_10
    ADD CONSTRAINT daily_usage_2026_10_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_11 daily_usage_2026_11_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_11
    ADD CONSTRAINT daily_usage_2026_11_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_11 daily_usage_2026_11_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_11
    ADD CONSTRAINT daily_usage_2026_11_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2026_12 daily_usage_2026_12_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_12
    ADD CONSTRAINT daily_usage_2026_12_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2026_12 daily_usage_2026_12_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2026_12
    ADD CONSTRAINT daily_usage_2026_12_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_01 daily_usage_2027_01_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_01
    ADD CONSTRAINT daily_usage_2027_01_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_01 daily_usage_2027_01_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_01
    ADD CONSTRAINT daily_usage_2027_01_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_02 daily_usage_2027_02_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_02
    ADD CONSTRAINT daily_usage_2027_02_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_02 daily_usage_2027_02_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_02
    ADD CONSTRAINT daily_usage_2027_02_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_03 daily_usage_2027_03_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_03
    ADD CONSTRAINT daily_usage_2027_03_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_03 daily_usage_2027_03_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_03
    ADD CONSTRAINT daily_usage_2027_03_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_04 daily_usage_2027_04_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_04
    ADD CONSTRAINT daily_usage_2027_04_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_04 daily_usage_2027_04_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_04
    ADD CONSTRAINT daily_usage_2027_04_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_05 daily_usage_2027_05_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_05
    ADD CONSTRAINT daily_usage_2027_05_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_05 daily_usage_2027_05_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_05
    ADD CONSTRAINT daily_usage_2027_05_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_06 daily_usage_2027_06_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_06
    ADD CONSTRAINT daily_usage_2027_06_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_06 daily_usage_2027_06_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_06
    ADD CONSTRAINT daily_usage_2027_06_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_07 daily_usage_2027_07_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_07
    ADD CONSTRAINT daily_usage_2027_07_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_07 daily_usage_2027_07_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_07
    ADD CONSTRAINT daily_usage_2027_07_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_08 daily_usage_2027_08_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_08
    ADD CONSTRAINT daily_usage_2027_08_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_08 daily_usage_2027_08_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_08
    ADD CONSTRAINT daily_usage_2027_08_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_09 daily_usage_2027_09_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_09
    ADD CONSTRAINT daily_usage_2027_09_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_09 daily_usage_2027_09_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_09
    ADD CONSTRAINT daily_usage_2027_09_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_10 daily_usage_2027_10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_10
    ADD CONSTRAINT daily_usage_2027_10_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_10 daily_usage_2027_10_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_10
    ADD CONSTRAINT daily_usage_2027_10_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_11 daily_usage_2027_11_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_11
    ADD CONSTRAINT daily_usage_2027_11_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_11 daily_usage_2027_11_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_11
    ADD CONSTRAINT daily_usage_2027_11_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: daily_usage_2027_12 daily_usage_2027_12_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_12
    ADD CONSTRAINT daily_usage_2027_12_pkey PRIMARY KEY (id, usage_date);


--
-- Name: daily_usage_2027_12 daily_usage_2027_12_project_id_billing_account_id_service_d_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_usage_2027_12
    ADD CONSTRAINT daily_usage_2027_12_project_id_billing_account_id_service_d_key UNIQUE (project_id, billing_account_id, service_description, usage_date);


--
-- Name: sync_logs sync_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_logs
    ADD CONSTRAINT sync_logs_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_alert_configs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_alert_configs_id ON public.alert_configs USING btree (id);


--
-- Name: ix_alert_incidents_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_alert_incidents_id ON public.alert_incidents USING btree (id);


--
-- Name: ix_alert_incidents_project_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_alert_incidents_project_id ON public.alert_incidents USING btree (project_id);


--
-- Name: ix_audit_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_logs_id ON public.audit_logs USING btree (id);


--
-- Name: ix_billing_accounts_billing_account_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_billing_accounts_billing_account_id ON public.billing_accounts USING btree (billing_account_id);


--
-- Name: ix_billing_accounts_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_billing_accounts_id ON public.billing_accounts USING btree (id);


--
-- Name: ix_sync_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sync_logs_id ON public.sync_logs USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: daily_usage_2024_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_01_pkey;


--
-- Name: daily_usage_2024_01_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_01_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_02_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_02_pkey;


--
-- Name: daily_usage_2024_02_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_02_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_03_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_03_pkey;


--
-- Name: daily_usage_2024_03_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_03_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_04_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_04_pkey;


--
-- Name: daily_usage_2024_04_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_04_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_05_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_05_pkey;


--
-- Name: daily_usage_2024_05_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_05_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_06_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_06_pkey;


--
-- Name: daily_usage_2024_06_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_06_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_07_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_07_pkey;


--
-- Name: daily_usage_2024_07_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_07_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_08_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_08_pkey;


--
-- Name: daily_usage_2024_08_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_08_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_09_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_09_pkey;


--
-- Name: daily_usage_2024_09_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_09_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_10_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_10_pkey;


--
-- Name: daily_usage_2024_10_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_10_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_11_pkey;


--
-- Name: daily_usage_2024_11_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_11_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2024_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2024_12_pkey;


--
-- Name: daily_usage_2024_12_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2024_12_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_01_pkey;


--
-- Name: daily_usage_2025_01_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_01_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_02_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_02_pkey;


--
-- Name: daily_usage_2025_02_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_02_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_03_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_03_pkey;


--
-- Name: daily_usage_2025_03_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_03_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_04_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_04_pkey;


--
-- Name: daily_usage_2025_04_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_04_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_05_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_05_pkey;


--
-- Name: daily_usage_2025_05_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_05_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_06_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_06_pkey;


--
-- Name: daily_usage_2025_06_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_06_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_07_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_07_pkey;


--
-- Name: daily_usage_2025_07_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_07_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_08_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_08_pkey;


--
-- Name: daily_usage_2025_08_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_08_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_09_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_09_pkey;


--
-- Name: daily_usage_2025_09_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_09_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_10_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_10_pkey;


--
-- Name: daily_usage_2025_10_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_10_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_11_pkey;


--
-- Name: daily_usage_2025_11_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_11_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2025_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2025_12_pkey;


--
-- Name: daily_usage_2025_12_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2025_12_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_01_pkey;


--
-- Name: daily_usage_2026_01_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_01_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_02_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_02_pkey;


--
-- Name: daily_usage_2026_02_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_02_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_03_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_03_pkey;


--
-- Name: daily_usage_2026_03_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_03_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_04_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_04_pkey;


--
-- Name: daily_usage_2026_04_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_04_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_05_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_05_pkey;


--
-- Name: daily_usage_2026_05_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_05_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_06_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_06_pkey;


--
-- Name: daily_usage_2026_06_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_06_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_07_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_07_pkey;


--
-- Name: daily_usage_2026_07_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_07_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_08_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_08_pkey;


--
-- Name: daily_usage_2026_08_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_08_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_09_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_09_pkey;


--
-- Name: daily_usage_2026_09_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_09_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_10_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_10_pkey;


--
-- Name: daily_usage_2026_10_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_10_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_11_pkey;


--
-- Name: daily_usage_2026_11_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_11_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2026_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2026_12_pkey;


--
-- Name: daily_usage_2026_12_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2026_12_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_01_pkey;


--
-- Name: daily_usage_2027_01_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_01_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_02_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_02_pkey;


--
-- Name: daily_usage_2027_02_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_02_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_03_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_03_pkey;


--
-- Name: daily_usage_2027_03_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_03_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_04_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_04_pkey;


--
-- Name: daily_usage_2027_04_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_04_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_05_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_05_pkey;


--
-- Name: daily_usage_2027_05_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_05_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_06_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_06_pkey;


--
-- Name: daily_usage_2027_06_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_06_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_07_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_07_pkey;


--
-- Name: daily_usage_2027_07_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_07_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_08_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_08_pkey;


--
-- Name: daily_usage_2027_08_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_08_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_09_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_09_pkey;


--
-- Name: daily_usage_2027_09_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_09_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_10_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_10_pkey;


--
-- Name: daily_usage_2027_10_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_10_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_11_pkey;


--
-- Name: daily_usage_2027_11_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_11_project_id_billing_account_id_service_d_key;


--
-- Name: daily_usage_2027_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.daily_usage_pkey ATTACH PARTITION public.daily_usage_2027_12_pkey;


--
-- Name: daily_usage_2027_12_project_id_billing_account_id_service_d_key; Type: INDEX ATTACH; Schema: public; Owner: postgres
--

ALTER INDEX public.uix_daily_usage ATTACH PARTITION public.daily_usage_2027_12_project_id_billing_account_id_service_d_key;


--
-- Name: alert_incidents alert_incidents_alert_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert_incidents
    ADD CONSTRAINT alert_incidents_alert_config_id_fkey FOREIGN KEY (alert_config_id) REFERENCES public.alert_configs(id);


--
-- Name: alert_incidents alert_incidents_handler_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alert_incidents
    ADD CONSTRAINT alert_incidents_handler_id_fkey FOREIGN KEY (handler_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 3Mmhdo0zLSF8kg4mgpncRbxFmthhw1mdld2e31f8dohBNBd5N9Xsfhi2ZuKQvWd

