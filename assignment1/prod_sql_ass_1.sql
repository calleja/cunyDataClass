create database ratings_movies;

\c ratings_movies


create table movie (movie_id smallserial PRIMARY KEY, title varchar(60));

create table critic(critic_id smallserial PRIMARY KEY, firstname varchar(40), 
lastname varchar(40), sex char(1));

create table movie_genres (movie_id_fkey smallint, genre varchar(50), 
primary key (movie_id_fkey,genre), FOREIGN KEY (movie_id_fkey) references
movie (movie_id));

create table movie_ratings(movie_id_fkey integer, critic_id_fkey integer, 
rating smallint, PRIMARY KEY (movie_id_fkey, critic_id_fkey),  FOREIGN KEY (movie_id_fkey) 
REFERENCES movie (movie_id) MATCH SIMPLE ON UPDATE CASCADE ON DELETE CASCADE, 
FOREIGN KEY (critic_id_fkey) 
REFERENCES critic (critic_id) MATCH SIMPLE ON UPDATE cascade ON DELETE cascade);

-- check the status of the database
/*
select distinct table_name from information_schema.columns 
where information_schema.columns.table_schema = 'public';
*/

-- INSERT statements
insert into movie (title) values ('Brooklyn'),
('Martian'),
('Jurassic World'),
('The Big Short'),
('Revenant'),
('The Hateful Eight');

insert into critic (firstname, lastname, sex) VALUES
('Emilio',	'Calleja',	'M'),
('Liliana',	'Calleja',	'F'),
('Andrey',	'Litvin',	'M'),
('Sarah',	'Welt',	'F'),
('Luis',	'Caridad',	'M');

INSERT INTO movie_genres (movie_id_fkey,genre) VALUES
(1,'drama'),(1,'romance'),		
(2,'adventure'),(2,'drama'),
(3,'action'), (3,'adventure'),(3,'Sci-fi'),(3,'thriller'),
(4,'biography'),(4,'comedy'),(4,'drama'),
(5,'adventure'),	(5,'Drama'),(5,'thriller'),(5,'western'),
(6,'Crime'),(6,'Drama'),(6,'Mystery');

-- Quality checking the inserts
/*
select movie.*, movie_genres.genre from movie 
join movie_genres on movie.movie_id=movie_genres.movie_id_fkey
where movie_id =5;

select column_name from information_schema.columns 
where table_schema = 'public' and table_name = 'critic';

select * from movie;
select * from critic;
*/
INSERT INTO movie_ratings (critic_id_fkey,movie_id_fkey, rating)
VALUES (1,1,3),
(1,2,5),
(1,3,4),
(1,4,5),
(1,5,3),
(1,6,2),
(2,1,3),
(2,2,5),
(2,3,4),
(2,4,4),
(2,5,3),
(2,6,1),
(3,1,1),
(3,2,4),
(3,3,4),
(3,4,4),
(3,5,5),
(3,6,4),
(4,1,5),
(4,2,4),
(4,3,2),
(4,4,3),
(4,5,3),
(4,6,3),
(5,1,5),
(5,2,4),
(5,3,2),
(5,4,3),
(5,5,4),
(5,6,3);