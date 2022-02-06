# HackerNews top50 stories API provider

This repository provides an application to fetch top 50 HackerNews stories where author's karma is more than 2413.

The application is a flask app with WSGI server ([waitress](https://docs.pylonsproject.org/projects/waitress/en/latest/)). 

`/stories` path is used for gathering HackerNews data. `/metrics` path exposing server metrics in a convenient format by using [prometheus_flask_exporter](https://github.com/rycus86/prometheus_flask_exporter) library. 
It also uses [requests-cache](https://requests-cache.readthedocs.io/en/stable/) library in order to reduce API response time. 

There is also a dashboard created and stored in `grafana.json` and can be easily imported to Grafana. \
Dashboard consists of 3 panels:
1) Total requests sorted by status
2) Average response time for requests in 1m range
3) (Test) Response time for the last request
> Note: Third panel will show only the last request latency, so it might not be handy if the number of requests in the scraping interval is more than 1.


## Prerequisites

- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) version v1.22.3+
- Access to a [kubernetes cluster](https://kubernetes.io/releases/download/) version v1.23.1+
- [Helm](https://helm.sh/docs/intro/install/) version v3.8.0


## Deploy Prometheus and Grafana (optional)



1. Add helm repository
   
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

2. Create namespace `prometheus` in which prometheus-operator will be installed

```
kubectl create ns prometheus
```

3. Install prometheus-operator (change namespace to the desired one or use default)

```
helm install prometheus prometheus-community/kube-prometheus-stack --namespace prometheus
```

> NB: log in to docker registry is required

## Deploy application and enable monitoring

1. Run `kube.sh` to deploy application

```
bash kube.sh
```
> Note: the script also exposes the application as a NodePort service and creates a servicemonitor if prometheus-operator exists

2. Enable proxy for grafana pod to access it from the local PC (default port 3000)

```
kubectl -n prometheus port-forward $(kubectl -n prometheus get pods  --selector=app.kubernetes.io/name=grafana  --output=jsonpath="{.items..metadata.name}")  3000
```

3. Login to Grafana and import `grafana.json` as a dashboard
> Default credentials: admin / prom-operator


## Verify

1. Deployment should have 3 pods running and you should be able to see hn-flask NodePort service

```
kubectl get all --selector=app=hn-flask
```

2. You should be able to access application by passing nodeport (31544 in this case) to cluster external IP and accessing the `/stories` path:

```
kubectl get service hn-flask
NAME       TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)           AGE
hn-flask   NodePort   10.97.116.219   <none>        57729:31544/TCP   77m
```
> Note: the url should look like this `https://127.0.0.1:31544/stories`


## Troubleshooting guide

1. Pods should be in running state
2. Service, deployment and servicemonitor should have the `app: hn-flask` label as configured in definition files
3. The targetPort of the service has changed to `57729`, the port of the hn-flask pods
4. If port `57729` is occupied by another service, it is feasible to alter to different one in the `main.py:L72`
5. Apps cache is set to never expire. It can be changed by providing a number of seconds to store the cache in the `expire_after` parameter in `main.py:L23`
6. In case of changing app configuration, you might want to rebuild the image. In this case, you may use the following command: \
`docker build --tag 551955/flask_hackernews:hn-flask2.3 .` from the repository folder
