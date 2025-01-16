# ImageToTreesXML
Console app for Windows and Linux, to create a trees.xml file, for use in the Cities: Skylines mod - GeoSkylines.

The console app reads the a image of much larger resolution then Cities: Skylines/Unity supports, in batches, and for each pixel, if the pixel color matches the mandatory defined filter, it writes the pixel position underneath the ID from the matched filter. 

To run the program you must first prepare a json configuration file, example shown in the provided `config_file_template.json` file. The config file indicates the path to the image, `trees_png_path`, and the filter, `colors_to_id`, as mentioned before.<br>
The filter is a list, which simply describes what pixel position to write underneath the `id` - integer, depending on the pixel `color` - hex string. 

This setup allows you to places one or more types of trees, depending on the pixel color or in this case, the id. 

Once you prepared the config file, copy the path to it and download the program from the releases page, depending on your OS. Once downloaded, run the program, input or paste in the path to the config file, press `Enter` and wait till the program generates the `tress.xml` file. The program also returns the number of generated trees, so make sure this count is less then the vanilla game trees limit ()250000) or a mod like `Tree Control 1.0` (2 million) supports.

See the Word document for details on how to use the generated `trees.xml` file.