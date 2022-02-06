#!/bin/bash
kubectl apply -f ./kube-definition-files/hn-flask-deploy.yaml
kubectl apply -f ./kube-definition-files/hn-flask-service.yaml

prometheus=`kubectl  get pods  --selector=app.kubernetes.io/name=prometheus  --output=jsonpath="{.items..metadata.name}" -A`
if [ -z "$prometheus" ]
then
    echo "Prometheus pods not found, skipping servicemonitor installation"
else
    kubectl apply -f ./kube-definition-files/hn-flask-servicemodule.yaml
fi
