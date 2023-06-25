CREATE TABLE Users(
	user_id serial primary key not null,
	username varchar(30) unique not null,
	password varchar(128) not null,
	user_delete_ind bool default false not null
);

CREATE TABLE Accounts(
	acc_id serial primary key not null,
	acc_name varchar(30) not null,
	acc_type varchar(8) not null,
	acc_bal decimal not null,
	acc_last_updated timestamp without time zone default now() not null,
	acc_delete_ind bool default false not null
);

CREATE TABLE UserAccounts(
	user_id int references Users(user_id) not null,
	acc_id int references Accounts(acc_id) not null,
	PRIMARY KEY (user_id, acc_id)
);


CREATE TABLE Transactions(
	trans_id serial primary key not null,
	acc_id int references Accounts(acc_id) not null,
	trans_type varchar(8) not null,
	trans_date timestamp without time zone default now() not null,
	trans_amt decimal not null,
	trans_notes varchar(256),
	trans_last_updated timestamp without time zone default now() not null,
	trans_delete_ind bool default false not null
);

CREATE TABLE UserTransactions(
	user_id int references Users(user_id) not null,
	trans_id int references Transactions(trans_id) not null,
	PRIMARY KEY (user_id, trans_id)
);