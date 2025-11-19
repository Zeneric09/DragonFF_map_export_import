# GTA DragonFF - Blender scripts to edit basic GTA formats
# Copyright (C) 2019  Parik

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bpy

from ..gtaLib.map import TextIPLData, MapDataUtility
from ..ops.cull_exporter import cull_exporter

#######################################################
class ipl_exporter:

    only_selected = False
    game_id = None
    export_inst = False
    export_cull = False

    inst_objects = []
    cull_objects = []
    total_objects_num = 0

    #######################################################
    @staticmethod
    def collect_objects(context):
        """Collect objects that have IPL data"""

        self = ipl_exporter

        self.inst_objects = []
        self.cull_objects = []

        for obj in context.scene.objects:
            if self.only_selected and not obj.select_get():
                continue

            if self.export_inst and obj.dff.type == 'OBJ':
                self.inst_objects.append(obj)

            if self.export_cull and obj.dff.type == 'CULL':
                self.cull_objects.append(obj)

        self.total_objects_num = len(self.inst_objects) + len(self.cull_objects)

    #######################################################
    @staticmethod
    def format_inst_line(obj):
        """Format an object as an inst line based on game version"""

        self = ipl_exporter
        
        # Get object properties
        obj_id = obj.dff.get('object_id', 0)
        model_name = obj.dff.get('model_name', obj.name.split('.')[0])
        interior = obj.dff.get('interior', 0)
        lod = obj.dff.get('lod', -1)
        
        # Get position
        pos = obj.location
        
        # Get rotation (quaternion)
        rot = obj.rotation_quaternion
        
        # Get scale (only for GTA III/VC)
        scale = obj.scale
        
        # Format based on game version
        from ..gtaLib.data.map_data import game_version
        
        if self.game_id == game_version.III:
            # GTA III: id, modelName, posX, posY, posZ, scaleX, scaleY, scaleZ, rotX, rotY, rotZ, rotW
            return f"{obj_id}, {model_name}, {pos.x}, {pos.y}, {pos.z}, {scale.x}, {scale.y}, {scale.z}, {rot.x}, {rot.y}, {rot.z}, {rot.w}"
        
        elif self.game_id == game_version.VC:
            # GTA VC: id, modelName, interior, posX, posY, posZ, scaleX, scaleY, scaleZ, rotX, rotY, rotZ, rotW
            return f"{obj_id}, {model_name}, {interior}, {pos.x}, {pos.y}, {pos.z}, {scale.x}, {scale.y}, {scale.z}, {rot.x}, {rot.y}, {rot.z}, {rot.w}"
        
        elif self.game_id == game_version.SA:
            # GTA SA: id, modelName, interior, posX, posY, posZ, rotX, rotY, rotZ, rotW, lod
            return f"{obj_id}, {model_name}, {interior}, {pos.x}, {pos.y}, {pos.z}, {rot.x}, {rot.y}, {rot.z}, {rot.w}, {lod}"
        
        else:
            # Default to SA format
            return f"{obj_id}, {model_name}, {interior}, {pos.x}, {pos.y}, {pos.z}, {rot.x}, {rot.y}, {rot.z}, {rot.w}, {lod}"

    #######################################################
    @staticmethod
    def export_ipl(filename):
        self = ipl_exporter

        self.collect_objects(bpy.context)

        if not self.total_objects_num:
            return

        object_instances = [self.format_inst_line(obj) for obj in self.inst_objects]
        cull_instacnes = cull_exporter.export_objects(self.cull_objects, self.game_id)

        ipl_Data = TextIPLData(
            object_instances,
            cull_instacnes,
        )

        MapDataUtility.write_ipl_data(filename, self.game_id, ipl_Data)

#######################################################
def export_ipl(options):
    """Main export function"""

    ipl_exporter.only_selected = options['only_selected']
    ipl_exporter.game_id       = options['game_id']
    ipl_exporter.export_inst   = options['export_inst']
    ipl_exporter.export_cull   = options['export_cull']

    ipl_exporter.export_ipl(options['file_name'])
