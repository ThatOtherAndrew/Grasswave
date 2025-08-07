# Synchrotron Documentation

## Quickstart

Firstly, ensure you've installed the [Synchrotron server](https://github.com/ThatOtherAndrew/Synchrotron) (TLDR: `pip install synchrotron`), and that
it is running:

```
synchrotron-server
```

Next, create some nodes with the following commands in the console:

```
new 440 freq;
new SineNode sine;
new PlaybackNode out;
```

Then use the below `link` commands, or connect the corresponding ports by dragging between ports in the graph UI:

```
link freq.out -> sine.frequency;
link sine.out -> out.left;
link sine.out -> out.right;
```

Finally click the `Start` button at the top right of the app (or use the `start` console command), and listen to the
lovely 440 Hz sine wave produced. 😌

<sub>Full Synchrolang language reference coming Soon™️</sub>

## Examples

You can find a few example graphs in the [`/examples` directory](https://github.com/ThatOtherAndrew/Synchrotron/tree/main/examples).

- The `.syn` files contain **no node positioning data** and will spew all the nodes into an ugly pile.
- The `.sui` files **_do_ have node positioning data**, and you can click `Choose file` > `Load` to dive in right away.
