## fig.service
systemd configuration file. Just drop it in and off ya go.

### Installation
```bash
$ cp fig.service /lib/systemd/system
$ sudo systemctl daemon-reload
$ sudo systemctl enable fig
$ sudo systemctl start fig
```