
`src/create_datapaths.py` fixes the paths or directories to run the pipeline. 


There are several options, either you can run directly

```
python src/create_datapaths.py
```

Or determine the configuration file inside `conf/datapaths`to be used and run

```
python src/create_datapaths.py datapaths=<configuration yaml>
```

The `<configuration yaml>` is read by `src/create_datapaths.py` as `cfg.datapaths`.

