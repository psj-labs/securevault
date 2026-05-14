#!/bin/bash
dnf remove -y runc
dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin --allowerasing
systemctl enable --now docker
