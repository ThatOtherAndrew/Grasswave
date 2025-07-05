# Synchrotron Documentation

## Quickstart

Firstly, ensure you've installed the [Synchrotron server](https://github.com/ThatOtherAndrew/Synchrotron), and that 
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
