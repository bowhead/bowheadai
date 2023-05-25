import config from 'config';

const ENVPATH = '.' + process.env.NODE_ENV;

/**
 * Returns the configuration value for the given option
 * @param  {String} configurationOption The configuration path, this is the equivalent of the config.get function
 * @return {Mixed}                     The configuration value if exists
 */
function GetConfig(configurationOption) {
  let configEnvPath = configurationOption + ENVPATH,
    configPath;

  if (config.has(configEnvPath)) {
    configPath = configEnvPath;
  } else {
    configPath = configurationOption;
  }

  return config.get(configPath);
}

export {
  GetConfig,
};