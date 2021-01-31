# Cron Jobs

This repo contains the cron jobs that run on my personal desktop. Everything runs via the [`run`](run) script, which sets up the environment and passes args to a python interpreter:

```sh
./run -m jobs.computer_facts
```

This jobs themselves live as python modules within [`jobs`](jobs/) directory.

The [`deploy`](deploy) script copies the jobs and necessary environment files to an untracked subdirectory, `deployed/`, and replaces the contents of my user crontab with whatever is in [`jobs.crontab`](jobs.crontab). 

The crontab ought to be set up to run things off of the deployed subdirectory, so that I can edit files locally with confidence that my currently running cron jobs are unaffected until deployment. 

## TODO

- [ ] This feels like a hacky reimplementation of airflow. If i end up caring about logging, etc, maybe I should implement a real solution.
- [ ] Set up linting and testing in deployment.
- [ ] Convert run/deploy scripts to Makefile targets.
