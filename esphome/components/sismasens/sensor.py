import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import CONF_ID

AUTO_LOAD = ["sensor"]

sismasens_ns = cg.esphome_ns.namespace("sismasens")
SismasensComponent = sismasens_ns.class_("SismasensComponent", cg.PollingComponent)

CONF_EARTHQUAKE = "earthquake"
CONF_COLLAPSE = "collapse"
CONF_SHUTOFF = "shutoff"
CONF_LAST_SI = "last_si"
CONF_LAST_PGA = "last_pga"
CONF_LAST_TEMP = "last_temp"
CONF_LAST_MAG = "last_mag"
CONF_INST_SI = "inst_si"
CONF_INST_PGA = "inst_pga"
CONF_INST_MAG = "inst_mag"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(SismasensComponent),

        cv.Optional(CONF_EARTHQUAKE): sensor.sensor_schema(),
        cv.Optional(CONF_COLLAPSE): sensor.sensor_schema(),
        cv.Optional(CONF_SHUTOFF): sensor.sensor_schema(),

        cv.Optional(CONF_LAST_SI): sensor.sensor_schema(),
        cv.Optional(CONF_LAST_PGA): sensor.sensor_schema(),
        cv.Optional(CONF_LAST_TEMP): sensor.sensor_schema(),
        cv.Optional(CONF_LAST_MAG): sensor.sensor_schema(),

        cv.Optional(CONF_INST_SI): sensor.sensor_schema(),
        cv.Optional(CONF_INST_PGA): sensor.sensor_schema(),
        cv.Optional(CONF_INST_MAG): sensor.sensor_schema(),
    }
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    if CONF_EARTHQUAKE in config:
        sens = await sensor.new_sensor(config[CONF_EARTHQUAKE])
        cg.add(var.set_earthquake_sensor(sens))

    if CONF_COLLAPSE in config:
        sens = await sensor.new_sensor(config[CONF_COLLAPSE])
        cg.add(var.set_collapse_sensor(sens))

    if CONF_SHUTOFF in config:
        sens = await sensor.new_sensor(config[CONF_SHUTOFF])
        cg.add(var.set_shutoff_sensor(sens))

    if CONF_LAST_SI in config:
        sens = await sensor.new_sensor(config[CONF_LAST_SI])
        cg.add(var.set_last_si_sensor(sens))

    if CONF_LAST_PGA in config:
        sens = await sensor.new_sensor(config[CONF_LAST_PGA])
        cg.add(var.set_last_pga_sensor(sens))

    if CONF_LAST_TEMP in config:
        sens = await sensor.new_sensor(config[CONF_LAST_TEMP])
        cg.add(var.set_last_temp_sensor(sens))

    if CONF_LAST_MAG in config:
        sens = await sensor.new_sensor(config[CONF_LAST_MAG])
        cg.add(var.set_last_mag_sensor(sens))

    if CONF_INST_SI in config:
        sens = await sensor.new_sensor(config[CONF_INST_SI])
        cg.add(var.set_inst_si_sensor(sens))

    if CONF_INST_PGA in config:
        sens = await sensor.new_sensor(config[CONF_INST_PGA])
        cg.add(var.set_inst_pga_sensor(sens))

    if CONF_INST_MAG in config:
        sens = await sensor.new_sensor(config[CONF_INST_MAG])
        cg.add(var.set_inst_mag_sensor(sens))
