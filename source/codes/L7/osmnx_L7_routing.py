# -*- coding: utf-8 -*-
"""
Osmnx routing by driving.

Created on Thu Dec  7 15:49:53 2017

@author: Henrikki Tenkanen
"""

# Network analysis in Python
# ==========================

# Finding a shortest path using a specific street network is a common GIS problem that has many practical
# applications. For example navigators are one of those "every-day" applications where **routing** using specific algorithms is used
# to find the optimal route between two (or multiple) points. 

# It is also possible to perform network analysis such as tranposrtation routing in Python. 
# `Networkx <https://networkx.github.io/documentation/stable/>`__ is a Python module that provides 
# a lot tools that can be used to analyze networks on various different ways. It also contains algorithms
# such as `Dijkstras algorithm <https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.shortest_paths.weighted.single_source_dijkstra.html#networkx.algorithms.shortest_paths.weighted.single_source_dijkstra>`__ or 
# `A* <https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.shortest_paths.astar.astar_path.html#networkx.algorithms.shortest_paths.astar.astar_path>`__ algoritm that are commonly used to find shortest paths along transportation network.

# To be able to conduct network analysis, it is, of course, necessary to have a network that is used for the analyses. 
# `Osmnx <https://github.com/gboeing/osmnx>`__ package that we just explored in previous tutorial, makes it really easy to 
# retrieve routable networks from OpenStreetMap with different transport modes (walking, cycling and driving). Osmnx also 
# combines some functionalities from ``networkx`` module to make it straightforward to conduct routing along OpenStreetMap data. 

# Next we will test the routing functionalities of osmnx by finding a shortest path between two points based on walking.

# Let's first download the OSM data from Kamppi but this time include only such street segments that are walkable. 
# In omsnx it is possible to retrieve only streets that are drivable by specifying ``'drive'`` into ``network_type`` parameter that can be used to 
# specify what kind of streets are retrieved from OpenStreetMap.

import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt

place_name = "Kamppi, Helsinki, Finland"
graph = ox.graph_from_place(place_name, network_type='drive')
fig, ax = ox.plot_graph(graph)

# Okey so now we have retrieved only such streets where it is possible to drive with a car. Let's confirm 
# this by taking a look at the attributes of the street network. Easiest way to do this is to convert the
# graph (nodes and edges) into GeoDataFrames.

edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)

# Let's check what columns do we have in our data
edges.columns

# Okey, so we have quite many columns in our GeoDataFrame. Most of the columns are fairly self-exploratory but the following table describes all of them.

# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | Column                                                         | Description                            | Data type              |
# +================================================================+========================================+========================+
# | `bridge <http://wiki.openstreetmap.org/wiki/Key:bridge>`__     | Bridge feature                         | boolean                |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | geometry                                                       | Geometry of the feature                | Shapely.geometry       |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `highway <http://wiki.openstreetmap.org/wiki/Key:highway>`__   | Tag for roads, paths (road type)       | str (list if multiple) |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `lanes <http://wiki.openstreetmap.org/wiki/Key:lanes>`__       | Number of lanes                        | int (or nan)           |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `lenght <http://wiki.openstreetmap.org/wiki/Key:length>`__     | The length of a feature in meters      | float                  |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `maxspeed <http://wiki.openstreetmap.org/wiki/Key:maxspeed>`__ | maximum legal speed limit              | int (list if multiple) | 
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `name <http://wiki.openstreetmap.org/wiki/Key:name>`__         | Name of the (street) element           | str (or nan)           |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `oneway <http://wiki.openstreetmap.org/wiki/Key:oneway>`__     | Street is usable only in one direction | boolean                |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `osmid <http://wiki.openstreetmap.org/wiki/Node>`__            | Unique node ids of the element         | list                   |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `u <http://ow.ly/bV8n30h7Ufm>`__                               | The first node of networkx edge tuple  | int                    |
# +----------------------------------------------------------------+----------------------------------------+------------------------+
# | `v <http://ow.ly/bV8n30h7Ufm>`__                               | The last node of networkx edge tuple   | int                    |
# +----------------------------------------------------------------+----------------------------------------+------------------------+

# Most of the attributes comes directly from the OpenStreetMap, however, columns ``u`` and ``v`` are networkx specific ids.  

# Let's take a look what kind of features we have in ``highway`` column.
edges['highway'].value_counts()
print("Coordinate system:", edges.crs)

# Okey, now we can confirm that as a result our street network indeed only contains such streets where it is allowed to drive with a car as there are no e.g. cycleways of footways included in the data. 
# We can also see that the CRS of the GeoDataFrame seems to be WGS84 (i.e. epsg: 4326).

# Let's continue and find the shortest path between two points based on the distance. As the data is in WGS84 format, we might first want to reproject our data into metric system so that our map looks better.
# Luckily there is a handy function in osmnx called ``project_graph()`` to project the graph data in UTM format. 
graph_proj = ox.project_graph(graph)
fig, ax = ox.plot_graph(graph_proj)

nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)
print("Coordinate system:", edges_proj.crs)
edges_proj.head()

# Okey, as we can see from the CRS the data is now in `UTM projection <https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system>`__ using zone 35 which is the one used for Finland, 
# and indeed the orientation of the map and the geometry values also confirm this. 

# Analyzing the network properties
# --------------------------------



# Shortest path analysis
# ----------------------

# Let's now calculate the shortest path between two points. First we need to specify the source and target locations
# for our route. Let's use the centroid of our network as the source location and the furthest point in East in our network as the target location.

# Let's first determine the centroid of our network. We can take advantage of the ``bounds`` attribute to find out the bounding boxes for each feature in our data. We then make a unary union of those features and make a bounding box geometry out of those values that enables us to determine the centroid of our data. 

# - This is what the bounds command gives us.
edges_proj.bounds.head()

# Okey so it is a DataFrame of minimum and maximum x- and y coordinates. Let's create a bounding box out of those.

from shapely.geometry import box
bbox = box(*edges_proj.unary_union.bounds)
print(bbox)

# Okey so as a result we seem to have a Polygon, but what actually happened here? First of all, we took the Geometries from our ``edges_proj`` GeoDataFrame (123 features) and made a unary union of those features (as a result we have a MultiLineString). 
# From the MultiLineString we can retrieve the maximum and minimum x and y coordinates of the geometry using the ``bounds`` attribute. 
# The bounds command returns a tuple of four coordinates (minx, miny, maxx, maxy). As a final step we feed those coordinates into box() function that creates a shapely.Polygon object out of those coordinates.
# The * -character is used to unpack the values from the tuple (`see details <https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists>`__)  

# - Now we can extract the centroid of our bounding box as the source location. 
orig_point = bbox.centroid
print(orig_point)

# Let's now find the eastestmost node in our street network. We can do this by calculating the x coordinates and finding out which node has the largest x-coordinate value. Let's ensure that the values are floats.
nodes_proj['x'] = nodes_proj.x.astype(float)
maxx = nodes_proj['x'].max()

# Let's retrieve the target Point having the largest x-coordinate. We can do this by using the .loc function of Pandas that we have used already many times in earlier tutorials.  
target_loc = nodes_proj.loc[nodes_proj['x']==maxx, :]
print(target_loc)

# Okey now we can see that as a result we have a GeoDataFrame with only one node and the information associated with it. Let's extract the Point geometry from the data. 
target_point = target_loc.geometry.values[0]
print(target_point)

# - Let's now find the nearest graph nodes (and their node-ids) to these points. 
# For osmnx we need to parse the coordinates of the Point as coordinate-tuple with Latitude, Longitude coordinates. 
# As our data is now projected to UTM projection, we need to specify with ``method`` parameter that the function uses 
# 'euclidean' distances to calculate the distance from the point to the closest node. 
# This becomes important if you want to know the actual distance between the Point and the closest node which you can retrieve by specifying parameter ``return_dist=True``.

orig_xy = (orig_point.y, orig_point.x)
target_xy = (target_point.y, target_point.x)
orig_node = ox.get_nearest_node(graph_proj, orig_xy, method='euclidean')
target_node = ox.get_nearest_node(graph_proj, target_xy, method='euclidean')

print(orig_node)
print(target_node)

o_closest = nodes_proj.loc[orig_node]
t_closest = nodes_proj.loc[target_node]

# Let's make a GeoDataFrame out of these series
od_nodes = gpd.GeoDataFrame([o_closest, t_closest], geometry='geometry', crs=nodes_proj.crs)

# Okey, as a result we got now the closest node-ids of our origin and target locations.
# Now we are ready to do the routing and find the shortest path between the origin and target locations 
# by using the ``shortest_path()`` `function <https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.shortest_paths.generic.shortest_path.html>`__ of networkx.

route = nx.shortest_path(G=graph_proj, source=orig_node, target=target_node, weight='distance')
print(route)

# Okey, as a result we get a list of all the nodes that are along the shortest path. We could extract the locations of those nodes from the ``nodes_proj`` GeoDataFrame and create a LineString presentation of the points, 
# but luckily osmnx can do that for us and we can plot shortest path by using ``plot_graph_route()`` function.
fig, ax = ox.plot_graph_route(graph_proj, route, origin_point=orig_xy, destination_point=target_xy)

# Awesome! Now we have a the shortest path between our origin and target locations. 
# Being able to analyze shortest paths between locations can be valuable information for many applications.
# Here, we only analyzed the shortest paths based on distance but quite often it is more useful to find the 
# optimal routes between locations based on the travelled time. Here, for example we could calculate the time that it takes
# to cross each road segment by dividing the length of the road segment with the speed limit and calculate the optimal routes by
# taking into account the speed limits as well that might alter the result especially on longer trips than here. 

# Saving shortest paths to disk
# -----------------------------

# Quite often you need to save the route e.g. as a Shapefile. 
# Hence, let's continue still a bit and see how we can make a Shapefile of our route with some information associated with it.  

# First we need to get the nodes that belong to the shortest path.
route_nodes = nodes_proj.loc[route]
print(route_nodes)

# Now we can create a LineString out of the Point geometries of the nodes
from shapely.geometry import LineString, Point
route_line = LineString(list(route_nodes.geometry.values))
print(route_line)

# Let's make a GeoDataFrame having some useful information about our route such as a list of the osmids that are part of the route and the length of the route. 
route_geom = gpd.GeoDataFrame(crs=edges_proj.crs)
route_geom['geometry'] = None
route_geom['osmids'] = None

# Let's add the information: geometry, a list of osmids and the length of the route.
route_geom.loc[0, 'geometry'] = route_line
route_geom.loc[0, 'osmids'] = str(list(route_nodes['osmid'].values))
route_geom['length_m'] = route_geom.length

# Now we have a GeoDataFrame that we can save to disk. Let's still confirm that everything is okey by plotting our route
# on top of our street network, and plot also the origin and target points on top of our map.

# Let's first prepare a GeoDataFrame for our origin and target points.
od_points = gpd.GeoDataFrame(crs=edges_proj.crs)
od_points['geometry'] = None
od_points['type'] = None
od_points.loc[0, ['geometry', 'type']] = orig_point, 'Origin'
od_points.loc[1, ['geometry', 'type']] = target_point, 'Target'
od_points.head()             

# Let's also get the buildings for our area and plot them as well.
buildings = ox.buildings_from_place(place_name)
buildings_proj = buildings.to_crs(crs=edges_proj.crs)

# Let's now plot the route and the street network elements to verify that everything is as it should. 
fig, ax = plt.subplots()
edges_proj.plot(ax=ax, linewidth=0.75, color='gray')
nodes_proj.plot(ax=ax, markersize=2, color='gray')
buildings_proj.plot(ax=ax, facecolor='khaki', alpha=0.7)
route_geom.plot(ax=ax, linewidth=4, linestyle='--', color='red')
od_points.plot(ax=ax, markersize=24, color='green')

plt.show()

# Great everything seems to be in order! As you can see, now we have a full 
# control of all the elements of our map and we can use all the aesthetic 
# properties that matplotlib provides to modify how our map will look like. 


