using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Xml.Serialization;

namespace GeoSkylines
{
    public class TreesXML
    {
        public int Width;
        public int Height;
        public int TreeCount;
        public string Mode;
        public List<int> ListID;
        public List<BufferedTreesCollection> Buffers;
    }

    public class BufferedTreesCollection
    {
        public List<BufferedTrees> BufferedTrees;
    }

    public class BufferedTrees
    {
        public int ID;
        public List<Position> Positions;
    }

    public class Position
    {
        public double X;
        public double Y;
    }
}
