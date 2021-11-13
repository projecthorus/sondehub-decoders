# Radiosonde Telemetry Frame Decoders

This repository is an attempt to collate the various sources of information on how to decode radiosonde telemetry frames into [one library](https://xkcd.com/927/), for use within SondeHub, allowing SondeHub to accept and decode raw data frames from clients.

The aim is to provide a set of Python modules which can be used to decode frames of telemetry from all common radiosonde types, producing data suitable for ingestion into the SondeHub DB. We will start with the 'best known' radiosonde - the RS41, then add support for other radiosonde types over (probably a very long) time.

Progress:
* RS41
  * Block Extraction - DONE
  * Blocks: 
    * Status Block - DONE
    * GPS Position - DONE
    * GPS Info - TODO
    * GPS Raw - TODO
    * XDATA - TODO
    * RS41-SGM Telemetry Block - TODO
    * Empty Block - TODO
    * Raw Measurement - DONE
  * SubFrame collation and decoding - TODO
  * PTU Calculations - TODO
    * Comparison against RS decoder.
  * Stateful Frame Decoder - TODO
* IMET-1/4
* IMET-54
* Graw DFM
* LMS6-1680
* LMS6-403
* M10
* M20
* iMS-100
* MRZ-H1
* RS92 (May not add support for this, as it is obsolete)

## Code Structure

This python lib is structured as follows:

* sondehubdecoders - Top level package
  * RS41 - RS41 frame decoder module.
    * decoder - RS41 frame decoder function: decoder(frame)
    * postprocess - Post-processing functions (GNSS position, sensor data)
  * utils - Checksum, data type, and GNSS coordinate conversion utilities, common to multiple radiosonde types

For all radiosonde types, there is a decode function (e.g. sondehubdecoders.RS41.decoder.decode()), which accepts a frame of telemetry data as bytes, and returns a dictionary. The contents of the returned dictionary will be different for each radiosonde type, but for all sonde types there will be a 'common' entry containing the basic information [required by SondeHub](https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format).

## Example Usage
Each decoder module has a helper main function allowing input of a telemetry frame as hex on the command line, e.g:
```
$ python -m sondehubdecoders.RS41.decoder 8635f44093df1a60cc726b2da8bfd2e25a3c0c722eed2ba358668c0a1012e146f66da43f6da6af407b03788afc655cee0a7355b3e21d67fe0f7928990553343631303438371e0000000000200000560003320444008089440000000000003c422ae9731d687a2a2ed402c8090296f402d06808a2510779590896c502c8090296f4020000000000000000000000000000005d6d7c1e8708d98fba1e0fb30b8011881cd40df818cf1eab0c8a0e91068e018313d792177d59c7fa3901ff91c6cc0bd06b00b817911f000000d4b7360073a8005da1c60179a50026fb660652da00269f3e119e56ff0aaec413a21801ec005b1bcb91ffea37eb0b9ad6003aada5136e53ff0977f41a51a4004200000090400084f57b156a2ea1e8db4aa91479b557eaf4ff1600fdff0a050ec4e676110000000000000000000000000000000000ecc7

{
    ... lots of data here
}
```

Each decoder module has a class (e.g. RS41) which allows ingestion of multiple frames of data, maintaining the latest state of the radiosonde.

### Resources Used
The following resources were a huge help in writing this library
* https://github.com/bazjo/RS41_Decoding
* https://github.com/rs1729/RS/