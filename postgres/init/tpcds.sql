-- TPC-DS Full Schema and Data Loading Script

-- Create TPC-DS schema
CREATE SCHEMA IF NOT EXISTS tpcds;

-- Table: call_center
CREATE TABLE IF NOT EXISTS tpcds.call_center (
    cc_call_center_sk int,
    cc_call_center_id varchar(16),
    cc_rec_start_date date,
    cc_rec_end_date date,
    cc_closed_date_sk int,
    cc_open_date_sk int,
    cc_name varchar(50),
    cc_class varchar(50),
    cc_employees int,
    cc_sq_ft int,
    cc_hours varchar(20),
    cc_manager varchar(40),
    cc_mkt_id int,
    cc_address_id int
);
COPY tpcds.call_center
FROM '/tpc-data/call_center.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: catalog_page
CREATE TABLE IF NOT EXISTS tpcds.catalog_page (
    cp_catalog_page_sk int,
    cp_catalog_page_id varchar(16),
    cp_start_date_sk int,
    cp_end_date_sk int,
    cp_department varchar(50),
    cp_catalog_number int,
    cp_catalog_page_number int,
    cp_description varchar(100),
    cp_type varchar(10)
);
COPY tpcds.catalog_page
FROM '/tpc-data/catalog_page.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: catalog_returns
CREATE TABLE IF NOT EXISTS tpcds.catalog_returns (
    cr_returned_date_sk int,
    cr_item_sk int,
    cr_refunded_cash numeric,
    cr_return_amt numeric,
    cr_fee numeric,
    cr_returned_customer_sk int,
    cr_order_number int,
    cr_returned_catalog_page_sk int,
    cr_ship_mode varchar(20)
);
COPY tpcds.catalog_returns
FROM '/tpc-data/catalog_returns.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: catalog_sales
CREATE TABLE IF NOT EXISTS tpcds.catalog_sales (
    cs_sold_date_sk int,
    cs_item_sk int,
    cs_warehouse_sk int,
    cs_item_sk2 int,
    cs_sales_price numeric,
    cs_ext_discount_amt numeric,
    cs_net_paid numeric,
    cs_net_paid_inc_tax numeric,
    cs_net_profit numeric
);
COPY tpcds.catalog_sales
FROM '/tpc-data/catalog_sales.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: customer
CREATE TABLE IF NOT EXISTS tpcds.customer (
    c_customer_sk int,
    c_customer_id varchar(16),
    c_current_cdemo_sk int,
    c_current_hdemo_sk int,
    c_current_addr_sk int,
    c_upper_case_customer_name varchar(100),
    c_first_purchase_date date,
    c_birth_day int,
    c_birth_month int,
    c_birth_year int,
    c_gender char(1)
);
COPY tpcds.customer
FROM '/tpc-data/customer.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: customer_address
CREATE TABLE IF NOT EXISTS tpcds.customer_address (
    ca_address_sk int,
    ca_address_id varchar(20),
    ca_street_number varchar(10),
    ca_street_name varchar(50),
    ca_street_type varchar(15),
    ca_suite_number varchar(10),
    ca_city varchar(50),
    ca_county varchar(50),
    ca_state varchar(20),
    ca_zip varchar(10),
    ca_country varchar(20),
    ca_gmt_offset numeric,
    ca_location_type varchar(20)
);
COPY tpcds.customer_address
FROM '/tpc-data/customer_address.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: customer_demographics
CREATE TABLE IF NOT EXISTS tpcds.customer_demographics (
    cd_demo_sk int,
    cd_gender char(1),
    cd_marital_status char(1),
    cd_education_status char(1),
    cd_purchase_estimate int,
    cd_credit_rating char(1),
    cd_dep_count int,
    cd_dep_employed_count int,
    cd_dep_college_count int
);
COPY tpcds.customer_demographics
FROM '/tpc-data/customer_demographics.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: date_dim
CREATE TABLE IF NOT EXISTS tpcds.date_dim (
    d_date_sk int,
    d_date_id varchar(16),
    d_date date,
    d_day_of_week varchar(10),
    d_month varchar(10),
    d_year int,
    d_dow numeric,
    d_moy numeric,
    d_dom numeric,
    d_qoy numeric,
    d_fy_year int,
    d_fy_quarter_num numeric,
    d_fy_week_num numeric,
    d_day_num_in_week numeric,
    d_day_num_in_month numeric,
    d_day_num_in_year numeric,
    d_week_num_in_year numeric,
    d_selling_season varchar(20),
    d_last_update date
);
COPY tpcds.date_dim
FROM '/tpc-data/date_dim.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: household_demographics
CREATE TABLE IF NOT EXISTS tpcds.household_demographics (
    hd_demo_sk int,
    hd_income_band_sk int,
    hd_buy_potential int,
    hd_dep_count int,
    hd_vehicle_count int
);
COPY tpcds.household_demographics
FROM '/tpc-data/household_demographics.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: income_band
CREATE TABLE IF NOT EXISTS tpcds.income_band (
    ib_income_band_sk int,
    ib_lower_bound numeric,
    ib_upper_bound numeric,
    ib_display_label varchar(50)
);
COPY tpcds.income_band
FROM '/tpc-data/income_band.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: inventory
CREATE TABLE IF NOT EXISTS tpcds.inventory (
    inv_date_sk int,
    inv_item_sk int,
    inv_warehouse_sk int,
    inv_quantity_on_hand int
);
COPY tpcds.inventory
FROM '/tpc-data/inventory.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: item
CREATE TABLE IF NOT EXISTS tpcds.item (
    i_item_sk int,
    i_item_id varchar(16),
    i_item_desc varchar(200),
    i_current_price numeric,
    i_wholesale_cost numeric,
    i_brand varchar(50),
    i_class varchar(50),
    i_category varchar(50),
    i_manufact_id int,
    i_manufact_desc varchar(100),
    i_size varchar(10),
    i_container varchar(25),
    i_manager_id int,
    i_product_name varchar(100)
);
COPY tpcds.item
FROM '/tpc-data/item.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: promotion
CREATE TABLE IF NOT EXISTS tpcds.promotion (
    p_promo_sk int,
    p_promo_id varchar(16),
    p_start_date_sk int,
    p_end_date_sk int,
    p_item_sk int,
    p_cost numeric,
    p_response_target numeric,
    p_promo_name varchar(100),
    p_channel_email char(1),
    p_channel_mail char(1),
    p_channel_catalog char(1),
    p_channel_tv char(1),
    p_channel_radio char(1)
);
COPY tpcds.promotion
FROM '/tpc-data/promotion.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: reason
CREATE TABLE IF NOT EXISTS tpcds.reason (
    r_reason_sk int,
    r_reason_id varchar(16),
    r_reason_desc varchar(100)
);
COPY tpcds.reason
FROM '/tpc-data/reason.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: ship_mode
CREATE TABLE IF NOT EXISTS tpcds.ship_mode (
    sm_ship_mode_sk int,
    sm_ship_mode_id varchar(16),
    sm_type varchar(20),
    sm_carrier varchar(20),
    sm_contract varchar(20)
);
COPY tpcds.ship_mode
FROM '/tpc-data/ship_mode.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: store
CREATE TABLE IF NOT EXISTS tpcds.store (
    s_store_sk int,
    s_store_id varchar(16),
    s_rec_start_date date,
    s_rec_end_date date,
    s_closed_date_sk int,
    s_store_name varchar(50),
    s_number_employees int,
    s_floor_space int,
    s_hours varchar(20),
    s_manager varchar(40),
    s_market_id int,
    s_geography_class varchar(20),
    s_market_desc varchar(100),
    s_market_manager varchar(40),
    s_division_id int,
    s_division_name varchar(50),
    s_company_id int,
    s_company_name varchar(50),
    s_street_number varchar(10),
    s_street_name varchar(50),
    s_street_type varchar(15),
    s_suite_number varchar(10),
    s_city varchar(50),
    s_county varchar(50),
    s_state varchar(20),
    s_zip varchar(10),
    s_country varchar(20),
    s_gmt_offset numeric,
    s_tax_precentage numeric
);
COPY tpcds.store
FROM '/tpc-data/store.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: store_returns
CREATE TABLE IF NOT EXISTS tpcds.store_returns (
    sr_returned_date_sk int,
    sr_item_sk int,
    sr_ticket_number int,
    sr_returned_customer_sk int,
    sr_return_amt numeric,
    sr_return_tax numeric,
    sr_fee numeric,
    sr_returned_date_sk2 int
);
COPY tpcds.store_returns
FROM '/tpc-data/store_returns.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: store_sales
CREATE TABLE IF NOT EXISTS tpcds.store_sales (
    ss_sold_date_sk int,
    ss_item_sk int,
    ss_ticket_number int,
    ss_quantity int,
    ss_wholesale_cost numeric,
    ss_list_price numeric,
    ss_sales_price numeric,
    ss_ext_discount_amt numeric,
    ss_net_paid numeric,
    ss_net_paid_inc_tax numeric,
    ss_net_profit numeric
);
COPY tpcds.store_sales
FROM '/tpc-data/store_sales.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: web_page
CREATE TABLE IF NOT EXISTS tpcds.web_page (
    wp_web_page_sk int,
    wp_web_page_id varchar(16),
    wp_rec_start_date date,
    wp_rec_end_date date,
    wp_creation_date_sk int,
    wp_access_date_sk int,
    wp_autogen_flag char(1),
    wp_link_count int,
    wp_char_count int,
    wp_revisit_count int,
    wp_type varchar(50)
);
COPY tpcds.web_page
FROM '/tpc-data/web_page.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: web_returns
CREATE TABLE IF NOT EXISTS tpcds.web_returns (
    wr_returned_date_sk int,
    wr_item_sk int,
    wr_ticket_number int,
    wr_returned_customer_sk int,
    wr_return_amt numeric,
    wr_reason_sk int
);
COPY tpcds.web_returns
FROM '/tpc-data/web_returns.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: web_sales
CREATE TABLE IF NOT EXISTS tpcds.web_sales (
    ws_sold_date_sk int,
    ws_item_sk int,
    ws_web_page_sk int,
    ws_web_site_sk int,
    ws_ticket_number int,
    ws_quantity int,
    ws_sales_price numeric,
    ws_ext_discount_amt numeric,
    ws_net_paid numeric,
    ws_net_paid_inc_tax numeric,
    ws_net_profit numeric
);
COPY tpcds.web_sales
FROM '/tpc-data/web_sales.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);

-- Table: web_site
CREATE TABLE IF NOT EXISTS tpcds.web_site (
    web_site_sk int,
    web_site_id varchar(16),
    web_rec_start_date date,
    web_rec_end_date date,
    web_name varchar(50),
    web_open_date_sk int,
    web_close_date_sk int,
    web_class varchar(50),
    web_manager varchar(40),
    web_market_id int,
    web_mkt_class varchar(50),
    web_mkt_desc varchar(100),
    web_market_manager varchar(40)
);
COPY tpcds.web_site
FROM '/tpc-data/web_site.dat'
WITH (
    FORMAT csv,
    DELIMITER '|',
    NULL ''
);
