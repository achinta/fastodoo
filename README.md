## fastodoo
Odoo is a popular open source ERP. FastAPI is a modern, fast (high-performance), web framework for building APIs with Python. FastOdoo aims to expose the odoo data as Rest API
for reading, while using Odoo ORM for updates. It reads the Odoo model and field metadata dynamically from ir_model_fields to minimize coding. 

## Getting started
Using docker
```shell
# Clone the repository and install the dependencies using poetry
git clone https://github.com/achinta/fastodoo.git
cd fastodoo
docker build . -f docker/fastodoo.Dockerfile

# modify the SQLALCHEMY_URL to point to your odoo database
docker run -p 80:80 -e SQLALCHEMY_URL=postgresql://odoo:odoo@host.docker.internal/odoo fastodoo
```

## Contribute
Currently it is very raw, with mainly the dynamic models implemented. Contributions, suggestions are welcome! Please look at issues for pending tasks. 

![Fast Odoo](https://static.swimlanes.io/0928d6faa52b9064f4e55ad44627c4c9.png)

## Demo
To run the demo on google cloud, we need three services (not ready yet)

##### 1. Postgres

##### 2. Odoo
TODO: add additional modules by default
```shell
# build docker container for odoo. Here we just add odoo.conf to set the database name and admin password. 
cd docker
docker build . -t odoo -f odoo.Dockerfile

# to run the container locally
docker run -p 8069:8069 --name odoo --link db:db -t odoo
```
    
##### 3. fastodoo