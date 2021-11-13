# Radiosonde Telemetry Frame Decoders

This repository is an attempt to collate the various sources of information on how to decode radiosonde telemetry frames into [one library](https://xkcd.com/927/), for use within SondeHub, allowing SondeHub to accept and decode raw data frames from clients.

The aim is to provide a set of Python modules which can be used to decode frames of telemetry from all common radiosonde types, producing data suitable for ingestion into the SondeHub DB. We will start with the 'best known' radiosonde - the RS41, then add support for other radiosonde types over (probably a very long) time.

Progress:
* RS41
  * Block Extraction - DONE
  * Blocks: 
    * Status Block - DONE
    * GPS Position - DONE
    * GPS Info - DONE
    * GPS Raw - TODO
    * XDATA - TODO
      * XDATA Telemetry Decoding - TODO
    * RS41-SGM Telemetry Block - TODO
    * Empty Block - TODO
    * Raw Measurement - DONE
  * SubFrame collation and decoding - PARTIAL
  * PTU Calculations
    * Temperature - Matches RS Decoder
    * Humidity - TODO
    * Pressure - TODO
    * Comparison against RS decoder - TODO
  * Stateful Frame Decoder - PARTIAL
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

## Example Usage (Single Frames)
Each decoder module has a helper main function allowing input of a telemetry frame as hex on the command line, e.g:

```
$ python -m sondehubdecoders.RS41.decoder 8635f44093df1a60cc726b2da8bfd2e25a3c0c722eed2ba358668c0a1012e146f66da43f6da6af407b03788afc655cee0a7355b3e21d67fe0f7928990553343631303438371e0000000000200000560003320444008089440000000000003c422ae9731d687a2a2ed402c8090296f402d06808a2510779590896c502c8090296f4020000000000000000000000000000005d6d7c1e8708d98fba1e0fb30b8011881cd40df818cf1eab0c8a0e91068e018313d792177d59c7fa3901ff91c6cc0bd06b00b817911f000000d4b7360073a8005da1c60179a50026fb660652da00269f3e119e56ff0aaec413a21801ec005b1bcb91ffea37eb0b9ad6003aada5136e53ff0977f41a51a4004200000090400084f57b156a2ea1e8db4aa91479b557eaf4ff1600fdff0a050ec4e676110000000000000000000000000000000000ecc7

{
    ... lots of data here
}
```

Each decoder module has a class (e.g. RS41) which allows ingestion of multiple frames of data, maintaining the latest state of the radiosonde.

## Example Usage (Multiple Frames)
If you have a file of raw data output from the RS decoders (e.g. what auto_rx can be [configured to save](https://github.com/projecthorus/radiosonde_auto_rx/blob/master/auto_rx/station.cfg.example#L408)), then these can be processed as follows:
```
$ python -m sondehubdecoders.utils.read_rs_raw example_data/S4610487_raw.hex | less

(lots of output here)

```
Adding the `-c` option results in a CSV output, with the same field ordering as auto_rx's log files.

## Test Frames

### RS41-SG
python -m sondehubdecoders.RS41.decoder 8635f44093df1a60cc726b2da8bfd2e25a3c0c722eed2ba358668c0a1012e146f66da43f6da6af407b03788afc655cee0a7355b3e21d67fe0f7928990553343631303438371e0000000000200000560003320444008089440000000000003c422ae9731d687a2a2ed402c8090296f402d06808a2510779590896c502c8090296f4020000000000000000000000000000005d6d7c1e8708d98fba1e0fb30b8011881cd40df818cf1eab0c8a0e91068e018313d792177d59c7fa3901ff91c6cc0bd06b00b817911f000000d4b7360073a8005da1c60179a50026fb660652da00269f3e119e56ff0aaec413a21801ec005b1bcb91ffea37eb0b9ad6003aada5136e53ff0977f41a51a4004200000090400084f57b156a2ea1e8db4aa91479b557eaf4ff1600fdff0a050ec4e676110000000000000000000000000000000000ecc7

### RS41-SGP
TODO

### RS41-SGM (encrypted)
python -m sondehubdecoders.RS41.decoder  8635f44093df1a60b078a0b1fdf4a364753dbfabeec1ea6fcf2d63a703cc95f46393de2b92bceef71c3a637c0a75a8137a081e28c374be730f7928e11c52303331303233321a000003000315000091000732324e6f91015f020700050bae012822000057da80a718eef5c8defbf6a97a7d42bad293c0594e6df47164eddf17668e5bb12903a1727a5fc819ed067fb475ce0405cb78a32de680de17479815fbca810716ad21e9c6ce065862e16df0bc64eed37ae889a9fe058e1047b9cf61042d5d0c5f311f6775fadee126efbac35832325c9fbcd3e172953c87a9bddc02481ed91b119857828b7490445d03253611b302b454ff3fe5bc6e37ffeab3c34a6d61b770f99445305f2871152c26d1fd478c762c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000789a

### RS41-SGM (unencrypted)
python -m sondehubdecoders.RS41.decoder   8635f44093df1a6005a0740a9f07945e94bcc728e3f26b139a1242196533e679a3c9d890a453be602759d62a27db88ee04818d504a98e43e0f7928b90b52303331303232381c00000100011600004f0007322a000000000000d5caa43d5da365397f87b4477f1b40400253040244ed02bb6508cd6107aa7008de360254040245ed02113f7c1e0608f860380a1ab320f410b315f412891bf708d514f9188c0afb0eb50fb4b2927d59351b37010825cf5a1df2d500494c59065b43ff54409b15dcd700d4f6c0090ccb0093908e1cb54dffe11e9a0240d8ff3338570ea64bffa3f88c053095005bfa9e1b89c7ff000000003a4900d6d0100fe9fefe72fb671ee0ee003bd47b15b4e06de8ab06ce1465da98ea35fa30f873fc0902103329762000000000000000000000000000000000000000000000000000000000000000004cf1

## Resources Used
The following resources were a huge help in writing this library
* https://github.com/bazjo/RS41_Decoding
* https://github.com/rs1729/RS/


