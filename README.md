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
    * RS41-SGM Telemetry Block - DONE
    * Empty Block - DONE
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
    * subframe - Subframe collation and parameter extraction
  * utils - Checksum, data type, and GNSS coordinate conversion utilities, common to multiple radiosonde types

For all radiosonde types, there is a decode function (e.g. sondehubdecoders.RS41.decoder.decode()), which accepts a frame of telemetry data as bytes, and returns a dictionary. The contents of the returned dictionary will be different for each radiosonde type, but for all sonde types there will be a 'common' entry containing the basic information [required by SondeHub](https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format).

## Dependencies
Either:
* sudo apt-get install python3-crcmod

or

* pip install crcmod

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

{'blocks': {'Empty Block': {'raw': b'\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00'},
            'GPS Fix Information': {'iTOW': 522693.001,
                                    'sv_quality': {2: 245,
                                                   6: 248,
                                                   11: 243,
                                                   12: 249,
                                                   14: 140,
                                                   15: 146,
                                                   17: 144,
                                                   19: 216,
                                                   24: 246,
                                                   28: 142,
                                                   29: 144,
                                                   32: 140},
                                    'timestamp_dt': datetime.datetime(2021, 11, 13, 1, 11, 33, 1000),
                                    'timestamp_str': '2021-11-13T01:11:33.001000',
                                    'week': 2183},
            'GPS Position': {'altitude': 697.6707692649215,
                             'ascent_rate': -9.277708048092673,
                             'ecef_pos_x_cm': -395746741,
                             'ecef_pos_y_cm': 342992404,
                             'ecef_pos_z_cm': -362971385,
                             'ecef_vel_x_cms': -247,
                             'ecef_vel_y_cms': -948,
                             'ecef_vel_z_cms': 999,
                             'ground_speed': 10.473563547062504,
                             'heading': 56.97657316759443,
                             'latitude': -34.90594509757247,
                             'longitude': 139.08463332510456,
                             'numSV': 8,
                             'pDOP': 1.6,
                             'sAcc': 40.0,
                             'wind_u': 8.781536401823903,
                             'wind_v': 5.707902574308551},
            'GPS Raw': {'raw': b'\xfa,=\x01\xff#\x97A\x06[b\xff\xa7{\\\x1a'
                               b'*\xef\x00\x04 \xe5\x049\x99\xff}\x9fv\x15V8'
                               b'\x01\xd3Z|\x11\x04\x07\x012wv\x0c\xb6\x07\x01c'
                               b'\x00\x00\x00\x0c4\x00\x9d\xa8\xf1\x1d\xea\t'
                               b'\x00\xb3\xa6p\x03&Q\x00\xbe\x1c5\t'
                               b'\x19\xb4\xff\xe9\xe3i\x1dj\xfe\x00\x8f\xe0'
                               b'\x85\x1c\x92]\xff'},
            'Measurements': {'humidity_main': 554184,
                             'humidity_ref1': 480272,
                             'humidity_ref2': 547976,
                             'humidity_temp_main': 175980,
                             'humidity_temp_ref1': 133630,
                             'humidity_temp_ref2': 193901,
                             'pressure_main': 0,
                             'pressure_ref1': 0,
                             'pressure_temp': 0.0,
                             'temp_meas_main': 180259,
                             'temp_meas_ref1': 133629,
                             'temp_meas_ref2': 193902,
                             'temperature': 7.269102149977816,
                             'unknown': 0,
                             'unknown2': 0},
            'Status': {'battery': 2.7,
                       'bitfield1': 3,
                       'bitfield2': 0,
                       'frame_count': 8583,
                       'humidity_sensor_heating_pwm': 140,
                       'max_subframe': 50,
                       'ref_area_temp': 22,
                       'serial': 'S4610487',
                       'subframe_count': 14,
                       'subframe_data': b'C\xf4\x0ci\xc3\x00\x00\x00'
                                        b'\x00\x00\x00\x00\x00\x00\x00\x00',
                       'tx_power': 7,
                       'unknown1': 0,
                       'unknown2': 0}},
 'common': {'alt': 697.6707692649215,
            'batt': 2.7,
            'burst_timer': 30600,
            'datetime': '2021-11-13T01:11:33.001000',
            'frame': 8583,
            'heading': 56.97657316759443,
            'lat': -34.90594509757247,
            'lon': 139.08463332510456,
            'sats': 8,
            'serial': 'S4610487',
            'subtype': 'RS41-SG',
            'type': 'RS41',
            'vel_h': 10.473563547062504,
            'vel_v': -9.277708048092673},
 'ecc_data': b'!p\xb1\xd8X\xcd\x83e;\x0c\xd0mIj\x9d.}\xb2\x93k\to\xc1\x9d'
             b'\x05\xc7\xb9uS\xd3\xadCb\xc4\x80\xd0\xe0\xf3\x95G'
             b'\xae\xa8\xc4\x9b;G\xf9\x14',
 'frame_type': 'Regular',
 'subframe': {'burstkill_status': 1,
              'burstkill_timer': 30600,
              'firmware_version': 20215,
              'freq_lower': 128,
              'freq_upper': 37,
              'humimeas_calT1': [1.2928862571716309,
                                 -0.03315814957022667,
                                 0.0050709364004433155],
              'humimeas_calT1_0': 1.2928862571716309,
              'humimeas_calT1_1': -0.03315814957022667,
              'humimeas_calT1_2': 0.0050709364004433155,
              'humimeas_co2': [-243.91079711914062,
                               0.18765400350093842,
                               8.199999683711212e-06],
              'humimeas_co2_0': -243.91079711914062,
              'humimeas_co2_1': 0.18765400350093842,
              'humimeas_co2_2': 8.199999683711212e-06,
              'mainboard_serial': 'S4431040\x000',
              'mainboard_type': 'RSM412',
              'pressure_serial': '00000000',
              'rf1': 750.0,
              'rf2': 1100.0,
              'subtype': 'RS41-SG',
              'tempmeas_calT1': [1.2429190874099731,
                                 -0.16472387313842773,
                                 0.008384902961552143],
              'tempmeas_calT1_0': 1.2429190874099731,
              'tempmeas_calT1_1': -0.16472387313842773,
              'tempmeas_calT1_2': 0.008384902961552143,
              'tempmeas_co1': [-243.91079711914062,
                               0.18765400350093842,
                               8.199999683711212e-06],
              'tempmeas_co1_0': -243.91079711914062,
              'tempmeas_co1_1': 0.18765400350093842,
              'tempmeas_co1_2': 8.199999683711212e-06,
              'tx_frequency_khz': 401500}}

(lots more output here)

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


