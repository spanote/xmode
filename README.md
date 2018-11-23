# xmode
Common Tools for Code Analysis

| Status       |
| ------------ |
| Experimental |

## Ready-to-use Tools

**xmode** provides the tool set ready for immediate use without extending the code.

At this stage, the tool is not yet ready in the form of a standalone command line tool. You will need to clone this repository to use it. For example, to get started,

```
git clone https://github.com/shiroyuki/xmode.git
```
```
pip3 install -r requirements.txt
```
```
cd xmode
```
> At this point, to use any tool, the syntax would be

```
g3 <subcommand>
```

See [the README file of Gallium project](https://github.com/shiroyuki/gallium) for more information.

### AWS Log Tailing `aws:logs:tail`

> Currently not really tailing but it is at least pull logs in the last 15 minutes.

#### Get Started

You can start by running

```bash
g3 aws:logs:tail -h
```

which will show you all available options.

#### Events

This tool allows you to tab into the data while **xmode** is still iterating through the events.

Suppose you want to filter the log messages manually.

You write `logs.py`.

```python
def warning_event_to_stdout(data):
    message = data['message'].strip()

    if '[WARNING]' in message:
        print(message)
```

To use it, just run this on your terminal.

```
g3 aws:logs:tail /aws/lambda/foo event:logs.warning_event_to_stdout
```

> The syntax is basically `EVENT_TYPE:PYTHON_PATH_TO_CALLBACK`. You can have more than one event handlers per event type.

Or suppose you want to print out something when the log pulling is done.

You now updated `logs.py`.

```python
def on_log_pulling_done():
    print()
```

To use it, just run this on your terminal.

```
g3 aws:logs:tail /aws/lambda/foo event:logs.warning_event_to_stdout done:on_log_pulling_done
```
