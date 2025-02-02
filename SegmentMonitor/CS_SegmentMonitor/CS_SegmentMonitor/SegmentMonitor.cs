﻿using ICities;
using UnityEngine;

namespace CS_SegmentMonitor
{
    class SegmentMonitor : IUserMod
    {
        public string Name => "Segment Traffic Monitor";

        public string Description => "Logs the traffic stats of each segment into a text file.";
    }
}
