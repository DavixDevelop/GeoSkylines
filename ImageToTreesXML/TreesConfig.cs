using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace GeoSkylines_ImageToJSON
{
    public class TreesConfig
    {
        [JsonProperty("trees_png_path")]
        public String TreesPngPath { get; set; }

        [JsonProperty("colors_to_id")]
        public List<ColorID> ColorsID { get; set; }

    }

    public class ColorID {
        [JsonProperty("color")]
        public String Color { get; set; }

        [JsonProperty("id")]
        public int ID { get; set; }
    }
}
