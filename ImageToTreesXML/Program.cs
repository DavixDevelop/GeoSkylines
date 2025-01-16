using SixLabors.ImageSharp;
using GeoSkylines_ImageToJSON;
using SixLabors.ImageSharp.PixelFormats;
using System.Collections;
using SixLabors.ImageSharp.Processing;
using Newtonsoft.Json;
using System.Xml.Serialization;

Console.WriteLine("Enter path to config file");
// C:\Users\david\Documents\Cities Skylines\Celje (Renwed)\trees_config.json
string? configFilePath = Console.ReadLine();

if (configFilePath != null) {
    TreesConfig treesConfig = null;

    using (StreamReader configFile = File.OpenText(configFilePath)) {
        JsonSerializer serializer = new JsonSerializer();
        treesConfig = (TreesConfig)serializer.Deserialize(configFile, typeof(TreesConfig));
    }

    if (treesConfig != null) {
        int tileSize = 512;
        string? rootPath = Path.GetDirectoryName(treesConfig.TreesPngPath);

        TreesXML treesXML = new TreesXML();
        treesXML.ListID = new List<int>();
        treesXML.TreeCount = 0;
        treesXML.Mode = "raster";

        Dictionary<string, int> colorID = new Dictionary<string, int>();
        foreach (ColorID col in treesConfig.ColorsID) {
            colorID.Add(Rgba32.ParseHex(col.Color).ToHex(), col.ID);
            treesXML.ListID.Add(col.ID);
        }

        Rgba32 color;
        string colorHex;
        int id;
        BufferedTrees bufferedTrees = new BufferedTrees();

        using (var image = Image.Load<Rgba32>(treesConfig.TreesPngPath)) {
            treesXML.Width = image.Width;
            treesXML.Height = image.Height;

            treesXML.Buffers = new List<BufferedTreesCollection>();

            for (int tileX = 0; tileX < image.Width; tileX += tileSize) {
                for (int tileY = 0; tileY < image.Height; tileY += tileSize) {
                    Image<Rgba32> tile = image.Clone(x => x.Crop(new Rectangle(tileX, tileY, (tileX + tileSize < image.Width) ? tileSize : image.Width - tileX, (tileY + tileSize < image.Height) ? tileSize : image.Height - tileY)));

                    BufferedTreesCollection _col = new BufferedTreesCollection();
                    _col.BufferedTrees = new List<BufferedTrees>();
                    Dictionary<string, BufferedTrees> colBufferedTrees = new Dictionary<string, BufferedTrees>();

                    for (int x = 0; x < tile.Width; x++) {
                        for (int y = 0; y < tile.Height; y++) {
                            color = tile[x, y];

                            if (color.R < 255f || color.G < 255f || color.B < 255f) {
                                colorHex = color.ToHex();

                                if (colorID.TryGetValue(colorHex, out id)) {

                                    if (!colBufferedTrees.TryGetValue(colorHex, out bufferedTrees)) {
                                        bufferedTrees = new BufferedTrees();
                                        bufferedTrees.ID = id;
                                        bufferedTrees.Positions = new List<Position>();
                                        colBufferedTrees.Add(colorHex, bufferedTrees);
                                    }

                                    bufferedTrees.Positions.Add(new Position() { X = tileX + x, Y = (image.Height - 1) - (tileY + y) });
                                    treesXML.TreeCount++;
                                    colBufferedTrees[colorHex] = bufferedTrees;

                                }
                            }

                        }
                    }

                    foreach (string col in colBufferedTrees.Keys) {
                        bufferedTrees = colBufferedTrees[col];
                        _col.BufferedTrees.Add(bufferedTrees);
                    }

                    if (_col.BufferedTrees.Count > 0)
                        treesXML.Buffers.Add(_col);
                }
            }
        }

        if(treesXML.Buffers != null && treesXML.Buffers.Count > 0 && rootPath != null) {
            string treesXMLPath = Path.Combine(rootPath, "trees.xml");

            using(TextWriter file = new StreamWriter(treesXMLPath, false)) {
                XmlSerializer serializer = new XmlSerializer(typeof(TreesXML));
                serializer.Serialize(file, treesXML);
                Console.WriteLine("trees config file written to: \n " + treesXMLPath);
            }
        }

        Console.ReadKey();
    }
}

