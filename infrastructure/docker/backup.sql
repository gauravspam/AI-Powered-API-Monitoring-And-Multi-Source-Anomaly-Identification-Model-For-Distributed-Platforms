--
-- PostgreSQL database dump
--

\restrict O6nUYozxvzdPlIRf76dsUB9DmdKmnlDGHo2OQ0L3RPKvlmWwtius0NRREqIje8C

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alert_rules; Type: TABLE; Schema: public; Owner: api_monitor
--

CREATE TABLE public.alert_rules (
    id bigint NOT NULL,
    alert_name character varying(255) NOT NULL,
    condition character varying(255) NOT NULL,
    created_at timestamp(6) without time zone NOT NULL,
    enabled boolean NOT NULL,
    notification_channels jsonb,
    threshold double precision,
    updated_at timestamp(6) without time zone
);


ALTER TABLE public.alert_rules OWNER TO api_monitor;

--
-- Name: alert_rules_id_seq; Type: SEQUENCE; Schema: public; Owner: api_monitor
--

CREATE SEQUENCE public.alert_rules_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_rules_id_seq OWNER TO api_monitor;

--
-- Name: alert_rules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: api_monitor
--

ALTER SEQUENCE public.alert_rules_id_seq OWNED BY public.alert_rules.id;


--
-- Name: anomaly_detections; Type: TABLE; Schema: public; Owner: api_monitor
--

CREATE TABLE public.anomaly_detections (
    id bigint NOT NULL,
    acknowledged_at timestamp(6) without time zone,
    acknowledged_by character varying(255),
    acknowledgement_note text,
    additional_context jsonb,
    anomaly_type character varying(100),
    api_log_id bigint,
    confidence_score double precision NOT NULL,
    created_at timestamp(6) without time zone NOT NULL,
    created_by character varying(255),
    deleted_at timestamp(6) without time zone,
    deleted_by character varying(255),
    endpoint character varying(500) NOT NULL,
    environment character varying(50),
    fusion_method character varying(100) NOT NULL,
    hybrid_ensemble_score double precision NOT NULL,
    is_acknowledged boolean,
    is_false_positive boolean,
    is_resolved boolean,
    marked_false_positive_at timestamp(6) without time zone,
    marked_false_positive_by character varying(255),
    http_method character varying(10) NOT NULL,
    ml_processing_time_ms bigint,
    ml_model_version character varying(50),
    msif_lstm_score double precision NOT NULL,
    ple_gru_score double precision NOT NULL,
    resolution_note text,
    resolved_at timestamp(6) without time zone,
    resolved_by character varying(255),
    service_name character varying(255),
    severity_level character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    trace_id character varying(255),
    updated_at timestamp(6) without time zone,
    updated_by character varying(255)
);


ALTER TABLE public.anomaly_detections OWNER TO api_monitor;

--
-- Name: anomaly_detections_id_seq; Type: SEQUENCE; Schema: public; Owner: api_monitor
--

CREATE SEQUENCE public.anomaly_detections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anomaly_detections_id_seq OWNER TO api_monitor;

--
-- Name: api_logs; Type: TABLE; Schema: public; Owner: api_monitor
--

CREATE TABLE public.api_logs (
    id bigint NOT NULL,
    anomaly_detection_id bigint,
    cpu_usage_percent double precision,
    created_at timestamp(6) without time zone NOT NULL,
    created_by character varying(255),
    day_of_week integer,
    deleted_at timestamp(6) without time zone,
    deleted_by character varying(255),
    disk_io_bytes bigint,
    endpoint character varying(500) NOT NULL,
    environment character varying(50),
    error_count integer,
    error_message text,
    error_rate double precision,
    hour_of_day integer,
    ip_address character varying(255),
    is_business_hours boolean,
    is_processed boolean NOT NULL,
    is_weekend boolean,
    memory_usage_percent double precision,
    metadata jsonb,
    http_method character varying(10) NOT NULL,
    ml_service_version character varying(50),
    network_io_bytes bigint,
    parent_span_id character varying(255),
    processed_at timestamp(6) without time zone,
    request_body jsonb,
    request_count integer,
    request_headers jsonb,
    request_size_bytes bigint,
    response_body jsonb,
    response_headers jsonb,
    response_size_bytes bigint,
    response_time_ms bigint NOT NULL,
    service_name character varying(255) NOT NULL,
    service_version character varying(50),
    span_id character varying(255),
    stack_trace text,
    status_code integer NOT NULL,
    trace_id character varying(255),
    updated_at timestamp(6) without time zone,
    updated_by character varying(255),
    user_agent text,
    user_id character varying(255)
);


ALTER TABLE public.api_logs OWNER TO api_monitor;

--
-- Name: api_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: api_monitor
--

CREATE SEQUENCE public.api_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_logs_id_seq OWNER TO api_monitor;

--
-- Name: distributed_traces; Type: TABLE; Schema: public; Owner: api_monitor
--

CREATE TABLE public.distributed_traces (
    id bigint NOT NULL,
    created_at timestamp(6) without time zone NOT NULL,
    duration_ms bigint,
    operation_name character varying(255),
    parent_span_id character varying(100),
    service_name character varying(255) NOT NULL,
    span_id character varying(100),
    status_code integer,
    tags text,
    "timestamp" timestamp(6) without time zone NOT NULL,
    trace_id character varying(100) NOT NULL
);


ALTER TABLE public.distributed_traces OWNER TO api_monitor;

--
-- Name: distributed_traces_id_seq; Type: SEQUENCE; Schema: public; Owner: api_monitor
--

CREATE SEQUENCE public.distributed_traces_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.distributed_traces_id_seq OWNER TO api_monitor;

--
-- Name: distributed_traces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: api_monitor
--

ALTER SEQUENCE public.distributed_traces_id_seq OWNED BY public.distributed_traces.id;


--
-- Name: system_metrics; Type: TABLE; Schema: public; Owner: api_monitor
--

CREATE TABLE public.system_metrics (
    id bigint NOT NULL,
    api_id bigint NOT NULL,
    cpu_usage double precision,
    error_rate double precision,
    memory_usage double precision,
    request_count integer,
    response_time_ms double precision,
    "timestamp" timestamp(6) without time zone NOT NULL
);


ALTER TABLE public.system_metrics OWNER TO api_monitor;

--
-- Name: system_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: api_monitor
--

CREATE SEQUENCE public.system_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_metrics_id_seq OWNER TO api_monitor;

--
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: api_monitor
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- Name: alert_rules id; Type: DEFAULT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.alert_rules ALTER COLUMN id SET DEFAULT nextval('public.alert_rules_id_seq'::regclass);


--
-- Name: distributed_traces id; Type: DEFAULT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.distributed_traces ALTER COLUMN id SET DEFAULT nextval('public.distributed_traces_id_seq'::regclass);


--
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- Data for Name: alert_rules; Type: TABLE DATA; Schema: public; Owner: api_monitor
--

COPY public.alert_rules (id, alert_name, condition, created_at, enabled, notification_channels, threshold, updated_at) FROM stdin;
\.


--
-- Data for Name: anomaly_detections; Type: TABLE DATA; Schema: public; Owner: api_monitor
--

COPY public.anomaly_detections (id, acknowledged_at, acknowledged_by, acknowledgement_note, additional_context, anomaly_type, api_log_id, confidence_score, created_at, created_by, deleted_at, deleted_by, endpoint, environment, fusion_method, hybrid_ensemble_score, is_acknowledged, is_false_positive, is_resolved, marked_false_positive_at, marked_false_positive_by, http_method, ml_processing_time_ms, ml_model_version, msif_lstm_score, ple_gru_score, resolution_note, resolved_at, resolved_by, service_name, severity_level, status, trace_id, updated_at, updated_by) FROM stdin;
3	\N	\N	\N	\N	\N	\N	0.6	2026-02-03 23:44:17.023388	system	\N	\N	test-api	production	conflict_detected	0.9797	f	f	f	\N	\N	POST	311	1.0.0	0.9797	0	\N	\N	\N	api-monitoring	CRITICAL	ACTIVE	\N	2026-02-03 23:44:17.023413	\N
4	\N	\N	\N	\N	\N	\N	0.6	2026-02-03 23:45:30.591458	system	\N	\N	test-api	production	conflict_detected	0.8809	f	f	f	\N	\N	POST	1914	1.0.0	0.8809	0	\N	\N	\N	api-monitoring	CRITICAL	ACTIVE	\N	2026-02-03 23:45:30.591482	\N
5	\N	\N	\N	\N	\N	\N	0.6	2026-02-03 23:46:31.644404	system	\N	\N	/api/users	production	conflict_detected	0.9108	f	f	f	\N	\N	GET	304	1.0.0	0.9108	0	\N	\N	\N	api-monitoring	CRITICAL	ACTIVE	\N	2026-02-03 23:46:31.644431	\N
6	\N	\N	\N	\N	\N	\N	0.6	2026-02-03 23:46:32.01106	system	\N	\N	/api/orders	production	conflict_detected	0.937	f	f	f	\N	\N	POST	309	1.0.0	0.937	0	\N	\N	\N	api-monitoring	CRITICAL	ACTIVE	\N	2026-02-03 23:46:32.011087	\N
7	\N	\N	\N	\N	\N	\N	0.6	2026-02-03 23:57:31.042078	system	\N	\N	docker-test	production	conflict_detected	0.8383	f	f	f	\N	\N	POST	1899	1.0.0	0.8383	0	\N	\N	\N	api-monitoring	CRITICAL	ACTIVE	\N	2026-02-03 23:57:31.042102	\N
\.


--
-- Data for Name: api_logs; Type: TABLE DATA; Schema: public; Owner: api_monitor
--

COPY public.api_logs (id, anomaly_detection_id, cpu_usage_percent, created_at, created_by, day_of_week, deleted_at, deleted_by, disk_io_bytes, endpoint, environment, error_count, error_message, error_rate, hour_of_day, ip_address, is_business_hours, is_processed, is_weekend, memory_usage_percent, metadata, http_method, ml_service_version, network_io_bytes, parent_span_id, processed_at, request_body, request_count, request_headers, request_size_bytes, response_body, response_headers, response_size_bytes, response_time_ms, service_name, service_version, span_id, stack_trace, status_code, trace_id, updated_at, updated_by, user_agent, user_id) FROM stdin;
\.


--
-- Data for Name: distributed_traces; Type: TABLE DATA; Schema: public; Owner: api_monitor
--

COPY public.distributed_traces (id, created_at, duration_ms, operation_name, parent_span_id, service_name, span_id, status_code, tags, "timestamp", trace_id) FROM stdin;
\.


--
-- Data for Name: system_metrics; Type: TABLE DATA; Schema: public; Owner: api_monitor
--

COPY public.system_metrics (id, api_id, cpu_usage, error_rate, memory_usage, request_count, response_time_ms, "timestamp") FROM stdin;
\.


--
-- Name: alert_rules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: api_monitor
--

SELECT pg_catalog.setval('public.alert_rules_id_seq', 1, false);


--
-- Name: anomaly_detections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: api_monitor
--

SELECT pg_catalog.setval('public.anomaly_detections_id_seq', 7, true);


--
-- Name: api_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: api_monitor
--

SELECT pg_catalog.setval('public.api_logs_id_seq', 1, false);


--
-- Name: distributed_traces_id_seq; Type: SEQUENCE SET; Schema: public; Owner: api_monitor
--

SELECT pg_catalog.setval('public.distributed_traces_id_seq', 1, false);


--
-- Name: system_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: api_monitor
--

SELECT pg_catalog.setval('public.system_metrics_id_seq', 1, false);


--
-- Name: alert_rules alert_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.alert_rules
    ADD CONSTRAINT alert_rules_pkey PRIMARY KEY (id);


--
-- Name: anomaly_detections anomaly_detections_pkey; Type: CONSTRAINT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.anomaly_detections
    ADD CONSTRAINT anomaly_detections_pkey PRIMARY KEY (id);


--
-- Name: api_logs api_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.api_logs
    ADD CONSTRAINT api_logs_pkey PRIMARY KEY (id);


--
-- Name: distributed_traces distributed_traces_pkey; Type: CONSTRAINT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.distributed_traces
    ADD CONSTRAINT distributed_traces_pkey PRIMARY KEY (id);


--
-- Name: system_metrics system_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: api_monitor
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_pkey PRIMARY KEY (id);


--
-- Name: idx_anomaly_detections_api_log_id; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_api_log_id ON public.anomaly_detections USING btree (api_log_id);


--
-- Name: idx_anomaly_detections_created_at; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_created_at ON public.anomaly_detections USING btree (created_at DESC);


--
-- Name: idx_anomaly_detections_endpoint; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_endpoint ON public.anomaly_detections USING btree (endpoint);


--
-- Name: idx_anomaly_detections_severity; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_severity ON public.anomaly_detections USING btree (severity_level);


--
-- Name: idx_anomaly_detections_severity_status; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_severity_status ON public.anomaly_detections USING btree (severity_level, status, created_at DESC);


--
-- Name: idx_anomaly_detections_status; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_status ON public.anomaly_detections USING btree (status);


--
-- Name: idx_anomaly_detections_trace_id; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_anomaly_detections_trace_id ON public.anomaly_detections USING btree (trace_id);


--
-- Name: idx_api_logs_created_at; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_created_at ON public.api_logs USING btree (created_at DESC);


--
-- Name: idx_api_logs_endpoint; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_endpoint ON public.api_logs USING btree (endpoint);


--
-- Name: idx_api_logs_endpoint_created; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_endpoint_created ON public.api_logs USING btree (endpoint, created_at DESC);


--
-- Name: idx_api_logs_service_created; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_service_created ON public.api_logs USING btree (service_name, created_at DESC);


--
-- Name: idx_api_logs_status_code; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_status_code ON public.api_logs USING btree (status_code);


--
-- Name: idx_api_logs_trace_id; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_trace_id ON public.api_logs USING btree (trace_id);


--
-- Name: idx_api_logs_unprocessed; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_api_logs_unprocessed ON public.api_logs USING btree (is_processed, created_at);


--
-- Name: idx_service_name; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_service_name ON public.distributed_traces USING btree (service_name);


--
-- Name: idx_timestamp; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_timestamp ON public.distributed_traces USING btree ("timestamp");


--
-- Name: idx_trace_id; Type: INDEX; Schema: public; Owner: api_monitor
--

CREATE INDEX idx_trace_id ON public.distributed_traces USING btree (trace_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO api_monitor;


--
-- PostgreSQL database dump complete
--

\unrestrict O6nUYozxvzdPlIRf76dsUB9DmdKmnlDGHo2OQ0L3RPKvlmWwtius0NRREqIje8C

