# couchbase-init

Automation to configure a couchbase cluster

Note: The Ansible Helper can be found here: [ansible-helper](https://github.com/mminichino/ansible-helper)

````
$ ansible-helper.py playbooks/couchbase-init.yaml -h host01,host02,host03 --domain domain.local --bucket ycsb --query 'CREATE PRIMARY INDEX ON `ycsb`;'
````
