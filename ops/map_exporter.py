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
import os

from ..gtaLib.map import TextIPLData, MapDataUtility
from ..ops.cull_exporter import cull_exporter

#######################################################
class map_exporter:

    only_selected = False
    game_id = None
    export_path = ""
    
    inst_objects = []
    cull_objects = []
    object_definitions = {}  # id -> definition
    total_objects_num = 0

    #######################################################
    @staticmethod
    def collect_objects(context):
        """Collect objects that have map data"""

        self = map_exporter

        self.inst_objects = []
        self.cull_objects = []
        self.object_definitions = {}

        for obj in context.scene.objects:
            if self.only_selected and not obj.select_get():
                continue

            if obj.dff.type == 'OBJ':
                # Only export objects with valid IDs (skip child meshes)
                obj_id = obj.dff.get('object_id', 0)
                if obj_id > 0:
                    self.inst_objects.append(obj)
                    
                    # Collect object definition
                    if obj_id not in self.object_definitions:
                        self.object_definitions[obj_id] = obj

            elif obj.dff.type == 'CULL':
                self.cull_objects.append(obj)

        self.total_objects_num = len(self.inst_objects) + len(self.cull_objects)

    #######################################################
    @staticmethod
    def format_inst_line(obj):
        """Format an object as an inst line based on game version"""

        self = map_exporter
        
        # Get object properties
        obj_id = obj.dff.get('object_id', 0)
        model_name = obj.dff.get('model_name', obj.name.split('.')[0])
        interior = obj.dff.get('interior', 0)
        lod = obj.dff.get('lod', -1)
        
        # Get position
        pos = obj.location
        
        # Get rotation (quaternion)
        if obj.rotation_mode == 'QUATERNION':
            rot = obj.rotation_quaternion
        else:
            rot = obj.rotation_euler.to_quaternion()
        
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
    def format_ide_objs_line(obj):
        """Format an object definition as an IDE objs line"""
        
        self = map_exporter
        
        obj_id = obj.dff.get('object_id', 0)
        model_name = obj.dff.get('model_name', obj.name.split('.')[0])
        txd_name = obj.dff.get('txd_name', model_name)
        draw_distance = obj.dff.get('draw_distance', 150)
        flags = obj.dff.get('flags', 0)
        
        # Simple format: id, modelName, txdName, drawDistance, flags
        return f"{obj_id}, {model_name}, {txd_name}, {draw_distance}, {flags}"

    #######################################################
    @staticmethod
    def export_ipl(ipl_filename):
        """Export IPL file"""
        
        self = map_exporter

        self.collect_objects(bpy.context)

        if not self.total_objects_num:
            return False

        object_instances = [self.format_inst_line(obj) for obj in self.inst_objects]
        cull_instances = cull_exporter.export_objects(self.cull_objects, self.game_id)

        ipl_data = TextIPLData(
            object_instances,
            cull_instances,
        )

        MapDataUtility.write_ipl_data(ipl_filename, self.game_id, ipl_data)
        return True

    #######################################################
    @staticmethod
    def export_ide(ide_filename):
        """Export IDE file"""
        
        self = map_exporter
        
        if not self.object_definitions:
            return False
        
        with open(ide_filename, 'w') as f:
            f.write("# IDE generated with DragonFF\n")
            f.write("objs\n")
            
            # Sort by ID for cleaner output
            sorted_ids = sorted(self.object_definitions.keys())
            for obj_id in sorted_ids:
                obj = self.object_definitions[obj_id]
                line = self.format_ide_objs_line(obj)
                f.write(f"{line}\n")
            
            f.write("end\n")
        
        return True

    #######################################################
    @staticmethod
    def export_map(ipl_filename, export_ide=True):
        """Export both IPL and IDE files"""
        
        self = map_exporter
        
        # Export IPL
        ipl_success = self.export_ipl(ipl_filename)
        
        if not ipl_success:
            return False
        
        # Export IDE if requested
        if export_ide and self.object_definitions:
            # Generate IDE filename from IPL filename
            ide_filename = os.path.splitext(ipl_filename)[0] + '.ide'
            self.export_ide(ide_filename)
        
        return True

#######################################################
def export_map(options):
    """Main export function"""

    map_exporter.only_selected = options.get('only_selected', False)
    map_exporter.game_id = options.get('game_id', 'SA')
    
    ipl_filename = options['file_name']
    export_ide = options.get('export_ide', True)
    
    return map_exporter.export_map(ipl_filename, export_ide)
