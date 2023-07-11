# PyThreeHeadsGenerator

This is a library that provides a function to procedurally generate dungeons in a specific way.

The input data are:
1. the size of the playing field
2. generation epicenter point
3. 'chance' parameter that defines the probability of continuing additional wirings after the first one during the dead ends processing.
4. 'c' parameter that defines the maximum number of heads spawned during the loop.

The output data are:
1. 2-dimensional bool array with common cells marked
2. 2-dimensional bool array with top-left corners of big cells marked
3. 2-dimensional bool array with doors used for horizontal movement marked
4. 2-dimensional bool array with doors used for vertical movement marked
5. the list of treasure positions

# The call example
```py
cells, big_cells, hor_doors, ver_doors, chests = rooms.generate(w, h, px, py, c=8)
```

# Model demonstrations
![image](https://github.com/ikudrickiy/PyThreeHeadsGenerator/assets/139219793/6dc3fd92-f8d4-4007-84b6-138afb273e86)
![image](https://github.com/ikudrickiy/PyThreeHeadsGenerator/assets/139219793/72041aed-4507-4738-92e8-5d204adb5581)
![image](https://github.com/ikudrickiy/PyThreeHeadsGenerator/assets/139219793/581b3f15-ac5f-46f8-8ffb-ed9ffd9cb215)

Animated algorithm demonstration video (click to see the video on YouTube):

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/qLQ_f9TnjgE/0.jpg)](https://www.youtube.com/watch?v=qLQ_f9TnjgE)
