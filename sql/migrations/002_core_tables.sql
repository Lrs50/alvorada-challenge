-- core: cleaned and typed rows, with keys.

create schema core;

create table core.customers (
    customer_id text primary key,
    customer_unique_id text not null,
    customer_state text not null
);

create table core.products (
    product_id text primary key,
    product_category_name text
);

create table core.orders (
    order_id text primary key,
    customer_id text not null references core.customers,
    order_status text not null,
    order_purchase_timestamp timestamp not null,
    order_delivered_customer_date timestamp
);

create table core.order_items (
    order_id text not null references core.orders,
    order_item_id integer not null,
    product_id text not null references core.products,
    price numeric(12, 2) not null,
    freight_value numeric(12, 2) not null,
    primary key (order_id, order_item_id)
);

create table core.order_payments (
    order_id text not null references core.orders,
    payment_sequential integer not null,
    payment_type text not null,
    payment_installments integer not null,
    payment_value numeric(12, 2) not null,
    primary key (order_id, payment_sequential)
);
