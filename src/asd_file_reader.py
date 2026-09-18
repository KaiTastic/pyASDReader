from __future__ import annotations

# !/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   ASD_File_Reader.py
@Time    :   2024/11/19 03:52:34
@Author  :   Kai Cao
@Version :   1.0.0
@Contact :   caokai_cgs@163.com
@License :   (C)Copyright 2024-
Copyright Statement:   Full Copyright
@Desc    :   According to "ASD File Format version 8: Revision B"
'''

import os
import struct
import re
import logging
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from collections import namedtuple
from enum import Enum
from .constant import (FileVersion_e, InstrumentType_e, InstrumentModel_e, SpectraType_e, SignatureState_e, AuditLogType_e, DataType_e, DataFormat_e, IT_ms_e, CalibrationType_e, SaturationError_e, ClassiferDataType_e)
from .logger_setup import setup_logging
from .file_attributes import FileAttributes

# Initialize module-level logger
log_file = f"asd_reader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
setup_logging(log_file, logging.INFO)
logger = logging.getLogger(__name__)

class ASDFile(FileAttributes):

    DEFAULT_DERIVATIVE_GAP = 5

    def __init__(self, filepath: str = None):
        """Initialize ASDFile instance.

        Args:
            filepath: Optional path to ASD file. If provided, file will be read automatically.
        """
        if filepath is not None:
            super().__init__(filepath)  # Initialize parent class

        self.asdFileVersion = 0
        self.metadata = None
        self.spectrumData = None
        self.referenceFileHeader = None
        self.referenceData = None
        self.classifierData = None
        self.dependants = None
        self.calibrationHeader = None
        self.calibrationSeriesABS = None
        self.calibrationSeriesBSE = None
        self.calibrationSeriesLMP = None
        self.calibrationSeriesFO = None
        self.auditLog = None
        self.signature = None
        self.__asdFileStream = None
        self.wavelengths = None

        # Auto-read file if filepath is provided
        if filepath is not None:
            self.read(filepath)

    def read(self: object, filePath: str) -> bool:
        readSuccess = False

        # Check if filePath is valid
        if filePath is None or not isinstance(filePath, (str, bytes, os.PathLike)):
            logger.error(f"Invalid file path: {filePath}")
            return False

        # Check if file exists
        if not (os.path.exists(filePath) and os.path.isfile(filePath)):
            logger.error(f"File does not exist or is not a file: {filePath}")
            return False

        try:
            # read in file to memory(buffer)
            with open(filePath, 'rb') as fileHandle:
                self.__asdFileStream = fileHandle.read()
                if self.__asdFileStream[-3:] == b'\xFF\xFE\xFD':
                    self.__bom = self.__asdFileStream[-3:]
                    self.__asdFileStream = self.__asdFileStream[:-3]
        except Exception as e:
            logger.exception(f"Error in reading the file.\nError: {e}")
            return False

        # refering C# Line 884 to identify the file version
        self.asdFileVersion, offset = self.__validate_fileVersion()

        # Check if file version is valid
        if self.asdFileVersion.value <= 0:
            logger.error(f"Invalid ASD file version")
            return False
        if self.asdFileVersion.value > 0:
            try:
                offset = self.__parse_metadata(offset)
                self.wavelengths = np.arange(self.metadata.channel1Wavelength, self.metadata.channel1Wavelength + self.metadata.channels * self.metadata.wavelengthStep, self.metadata.wavelengthStep)
            except Exception as e:
                logger.exception(f"Error in parsing the metadata.\nError: {e}")
            else:
                try:
                    offset = self.__parse_spectrumData(offset)
                except Exception as e:
                    logger.exception(f"Error in parsing the metadata and spectrum data.\nError: {e}")
        if self.asdFileVersion.value >= 2:
            try:
                offset = self.__parse_referenceFileHeader(offset)
            except Exception as e:
                logger.exception(f"Error in parsing the reference file header.\nError: {e}")
            else:
                try:
                    offset = self.__parse_referenceData(offset)
                except Exception as e:
                    logger.exception(f"Error in parsing the reference data.\nError: {e}")
        if self.asdFileVersion.value >= 6:
            try:
                # Read Classifier Data
                offset = self.__parse_classifierData(offset)
            except Exception as e:
                logger.exception(f"Error in parsing the classifier data.\nError: {e}")
            else:
                try:
                    offset = self.__parse_dependentVariables(offset)
                except Exception as e:
                    logger.exception(f"Error in parsing the depndant variables.\nError: {e}")
        if self.asdFileVersion.value >= 7:
            try:
                # Read Calibration Header
                offset = self.__parse_calibrationHeader(offset)
            except Exception as e:
                logger.exception(f"Error in parsing the calibration header.\nError: {e}")
            else:
                try:
                    if self.calibrationHeader and (self.calibrationHeader.calibrationNum > 0):
                        # Parsing the calibration data according to 'ASD File Format version 8: Revision B', through the suquence of 'Absolute Calibration Data', 'Base Calibration Data', 'Lamp Calibration Data', 'Fiber Optic Data' successively.
                        for hdr in self.calibrationHeader.calibrationSeries:  # Number of calibrationSeries buffers in the file.
                            if hdr[0] == CalibrationType_e.cb_ABSOLUTE:
                                self.calibrationSeriesABS, _, _, offset = self.__parse_spectra(offset)
                            elif hdr[0] == CalibrationType_e.cb_BASE:
                                self.calibrationSeriesBSE, _, _, offset = self.__parse_spectra(offset)
                            elif hdr[0] == CalibrationType_e.cb_LAMP:
                                self.calibrationSeriesLMP, _, _, offset = self.__parse_spectra(offset)
                            elif hdr[0] == CalibrationType_e.cb_FIBER:
                                self.calibrationSeriesFO, _, _, offset = self.__parse_spectra(offset)
                    # else:
                    #     logger.info(f"Calibration data is not available.")
                except Exception as e:
                    logger.exception(f"Error in parsing the calibration data.\nError: {e}")       
        if self.asdFileVersion.value >= 8:
            try:
                # Read Audit Log
                offset = self.__parse_auditLog(offset)
            except Exception as e:
                logger.exception(f"Error in parsing the audit log.\nError: {e}")
                # Read Signature
            else:
                try:
                    offset = self.__parse_signature(offset)
                except Exception as e:
                    logger.exception(f"Error in parsing the signature.\nError: {e}")
        readSuccess = True
        return readSuccess

    def update(self, field_name: str, new_value):
        pass
        
    def write(self: object, file: str) -> bool:
        pass

    def __check_offset(func):
        def wrapper(self: object, offset: int = None, *args, **kwargs):
            # Check if offset is None or out of range
            # TODO: add 0 <= offset < len(self.__asdFileStream) check                
            if isinstance(offset, int) and 0 <= offset:
                if offset < len(self.__asdFileStream):
                    return func(self, offset, *args, **kwargs)
                else:
                    logger.info("Reached the end of the binary byte stream. offset: {offset}")
                    return None, None
            else:
                logger.error(f"Invalid offset: {offset}. It should be a non-negative integer.")
                return None, None
        return wrapper
    
    @__check_offset
    def __parse_metadata(self: object, offset) -> int:

        asdMetadataFormat = '<157s 18s B B b b l b l f f b b b b b H 128s 56s L h h H H f f f f h b 4b H H H b L H H H H f f 27s 5b'
        asdMetadatainfo = namedtuple('metadata', "asdFileVersion comments when_datetime daylighSavingsFlag programVersion fileVersion iTime \
        darkCorrected darkTime dataType referenceTime channel1Wavelength wavelengthStep dataFormat \
        old_darkCurrentCount old_refCount old_sampleCount application channels appData gpsData \
        intergrationTime_ms fo darkCurrentCorrention calibrationSeries instrumentNum yMin yMax xMin xMax \
        ipNumBits xMode flags1 flags2 flags3 flags4 darkCurrentCount refCount sampleCount instrument \
        calBulbID swir1Gain swir2Gain swir1Offset swir2Offset splice1_wavelength splice2_wavelength smartDetectorType \
        spare1 spare2 spare3 spare4 spare5 byteStream byteStreamLength")
        try:
            comments, when, programVersion, fileVersion, iTime, darkCorrected, darkTime, \
            dataType, referenceTime, channel1Wavelength, wavelengthStep, dataFormat, \
            old_darkCurrentCount, old_refCount, old_sampleCount, \
            application, channels, appData, gpsData, intergrationTime_ms, fo, darkCurrentCorrention, \
            calibrationSeries, instrumentNum, yMin, yMax, xMin, xMax, ipNumBits, xMode, \
            flags1, flags2, flags3, flags4, darkCurrentCount, refCount, \
            sampleCount, instrument, calBulbID, swir1Gain, swir2Gain, swir1Offset, swir2Offset, \
            splice1_wavelength, splice2_wavelength, smartDetectorType, \
            spare1, spare2, spare3, spare4, spare5 = struct.unpack_from(asdMetadataFormat, self.__asdFileStream, offset)
            asdFileVersion, _ = self.__validate_fileVersion()
            comments = comments.strip(b'\x00') # remove null bytes
            # Parse the time from the buffer, format is year, month, day, hour, minute, second
            when_datetime, daylighSavingsFlag = self.__parse_ASDFilewhen((struct.unpack_from('9h', when)))  # 9 short integers
            programVersion = self.__parseVersion(programVersion)
            fileVersion = self.__parseVersion(fileVersion)
            darkCorrected = bool(darkCorrected)
            darkTime = datetime.fromtimestamp(darkTime) 
            dataType = DataType_e(dataType)
            referenceTime = datetime.fromtimestamp(referenceTime)
            dataFormat = DataFormat_e(dataFormat)
            intergrationTime = IT_ms_e(intergrationTime_ms)
            calibrationSeries = CalibrationType_e(calibrationSeries)
            flags2 = self.__parseSaturationError(flags2)
            instrument = InstrumentType_e(instrument)
            ByteStream = self.__asdFileStream[:484]
            ByteStreamLength = len(ByteStream)
            offset += struct.calcsize(asdMetadataFormat)
            self.metadata = asdMetadatainfo._make(
                (asdFileVersion, comments, when_datetime, daylighSavingsFlag, programVersion, fileVersion, iTime, darkCorrected, darkTime, \
                dataType, referenceTime, channel1Wavelength, wavelengthStep, dataFormat, old_darkCurrentCount, old_refCount, old_sampleCount, \
                application, channels, appData, gpsData, intergrationTime, fo, darkCurrentCorrention, calibrationSeries, instrumentNum, \
                yMin, yMax, xMin, xMax, ipNumBits, xMode, flags1, flags2, flags3, flags4, darkCurrentCount, refCount, \
                sampleCount, instrument, calBulbID, swir1Gain, swir2Gain, swir1Offset, swir2Offset, \
                splice1_wavelength, splice2_wavelength, smartDetectorType, \
                spare1, spare2, spare3, spare4, spare5 , ByteStream, ByteStreamLength))
        except Exception as e:
            logger.exception(f"Metadata (ASD File Header) parse error: {e}")
            return None
        # logger.info(f"Read: metadata end offset: {offset}")
        return offset
            
    @__check_offset
    def __parse_spectrumData(self: object, offset: int) -> int:
        try:
            spectrumDataInfo = namedtuple('spectrumData', 'spectra byteStream byteStreamLength')
            spectra, spectrumDataStream, spectrumDataStreamLength, offset = self.__parse_spectra(offset)
            self.spectrumData = spectrumDataInfo._make((spectra, spectrumDataStream, spectrumDataStreamLength))
            # logger.info(f"Read: spectrum data end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"Spectrum Data parse error: {e}")
            return None

    @__check_offset
    def __parse_referenceFileHeader(self: object, offset: int) -> int:
        initOffset = offset
        asdReferenceFormat = 'd d'
        asdreferenceFileHeaderInfo = namedtuple('referenceFileHeader', "referenceFlag referenceTime spectrumTime referenceDescription byteStream byteStreamLength")
        try:
            referenceFlag, offset = self.__parse_Bool(offset)
            referenceTime_doublefloat, spectrumTime_doublefloat = struct.unpack_from(asdReferenceFormat, self.__asdFileStream, offset)
            referenceTime_datetime = self.__parseTimeOLE(referenceTime_doublefloat)  # Convert to datetime
            spectrumTime_datetime = self.__parseTimeOLE(spectrumTime_doublefloat)    # Convert to datetime
            offset += struct.calcsize(asdReferenceFormat)
            referenceDescription, offset = self.__parse_bstr(offset)
            byteStream = self.__asdFileStream[initOffset:offset]
            byteStreamLength = len(byteStream)
            self.referenceFileHeader = asdreferenceFileHeaderInfo._make((referenceFlag, referenceTime_datetime, spectrumTime_datetime, referenceDescription, byteStream, byteStreamLength))
            # logger.info(f"Read: reference file header end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"Reference File Header parse error: {e}")
            return None

    @__check_offset
    def __parse_referenceData(self: object, offset: int) -> int:
        try:
            referenceDataInfo = namedtuple('referenceData', 'spectra byteStream byteStreamLength')
            spectra, referenceDataStream, referenceDataStreamLength, offset = self.__parse_spectra(offset)
            self.referenceData = referenceDataInfo._make((spectra, referenceDataStream, referenceDataStreamLength))
            # logger.info(f"Read: reference data end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"Reference Data parse error: {e}")
            return None

    @__check_offset
    def __parse_classifierData(self: object, offset: int) -> int:
        try:
            initOffset = offset
            yCode, yModelType = struct.unpack_from('bb', self.__asdFileStream, offset)
            offset += struct.calcsize('bb')
            title_str, offset = self.__parse_bstr(offset)
            subtitle_str, offset = self.__parse_bstr(offset)
            productName_str, offset = self.__parse_bstr(offset)
            vendor_str, offset = self.__parse_bstr(offset)
            lotNumber_str, offset = self.__parse_bstr(offset)
            sample__str, offset = self.__parse_bstr(offset)
            modelName_str, offset = self.__parse_bstr(offset)
            operator_str, offset = self.__parse_bstr(offset)
            dateTime_str, offset = self.__parse_bstr(offset)
            instrument_str, offset = self.__parse_bstr(offset)
            serialNumber_str, offset = self.__parse_bstr(offset)
            displayMode_str, offset = self.__parse_bstr(offset)
            comments_str, offset = self.__parse_bstr(offset)
            units_str, offset = self.__parse_bstr(offset)
            filename_str, offset = self.__parse_bstr(offset)
            username_str, offset = self.__parse_bstr(offset)
            reserved1_str, offset = self.__parse_bstr(offset)
            reserved2_str, offset = self.__parse_bstr(offset)
            reserved3_str, offset = self.__parse_bstr(offset)
            reserved4_str, offset = self.__parse_bstr(offset)
            constituantCount_int, = struct.unpack_from('H', self.__asdFileStream, offset)
            offset += struct.calcsize('H')
            asdClassifierDataInfo = namedtuple('classifierData', 'yCode yModelType title subtitle productName vendor lotNumber sample modelName operator dateTime instrument serialNumber displayMode comments units filename username reserved1 reserved2 reserved3 reserved4 constituantCount constituantItems byteStream byteStreamLength')
            # Past the constituants
            if constituantCount_int > 0:
                offset += 10
                # logger.info(f"constituant items ")
                constituantItems = []
                for i in range(constituantCount_int):
                    # logger.info(f"constituant items sequence: {i}")
                    item, offset = self.__parse_constituantType(offset)
                    constituantItems.append(item)
            if constituantCount_int == 0:
                constituantItems = []
                offset += 2 
            byteStream = self.__asdFileStream[initOffset:offset]
            byteStreamLength = len(byteStream)
            self.classifierData = asdClassifierDataInfo._make((yCode, yModelType, title_str, subtitle_str, productName_str, vendor_str, lotNumber_str, sample__str, modelName_str, operator_str, dateTime_str, instrument_str, serialNumber_str, displayMode_str, comments_str, units_str, filename_str, username_str, reserved1_str, reserved2_str, reserved3_str, reserved4_str, constituantCount_int, constituantItems, byteStream, byteStreamLength))
            # logger.info(f"Read: classifier Data end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"classifier Data parse error: {e}")
            return None

    @__check_offset
    def __parse_dependentVariables(self: object, offset: int) -> int:
        try:
            initOffset = offset
            dependantInfo = namedtuple('dependants', 'saveDependentVariables dependentVariableCount dependentVariableLabels dependentVariableValue byteStream byteStreamLength')
            saveDependentVariables, offset = self.__parse_Bool(offset)
            dependant_format = 'h'
            dependentVariableCount, = struct.unpack_from(dependant_format, self.__asdFileStream, offset)
            offset += struct.calcsize(dependant_format)
            if dependentVariableCount > 0:
                offset += 10
                dependantVariableLabels_list = []
                for i in range(dependentVariableCount):
                    dependentVariableLabel, offset = self.__parse_bstr(offset)
                    dependantVariableLabels_list.append(dependentVariableLabel)
                offset += 10
                dependantVariableValues_list = []
                for i in range(dependentVariableCount):
                    dependentVariableValue, = struct.unpack_from('<f', self.__asdFileStream, offset)
                    dependantVariableValues_list.append(dependentVariableValue)
                    offset += struct.calcsize('<f')
                self.dependants = dependantInfo._make((saveDependentVariables, dependentVariableCount, dependantVariableLabels_list, dependantVariableValues_list, self.__asdFileStream[initOffset:offset], len(self.__asdFileStream[initOffset:offset])))
            # if there are no dependent variables, skip 4 bytes (corresponding to 4 empty byte positions b'\x00')
            if dependentVariableCount == 0:
                offset += 4
                dependantVariableLabels_list = []
                dependantVariableValues_list = []
                self.dependants = dependantInfo._make((saveDependentVariables, dependentVariableCount, dependantVariableLabels_list, dependantVariableValues_list, self.__asdFileStream[initOffset:offset], len(self.__asdFileStream[initOffset:offset])))
            # logger.info(f"Read: dependant variables end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"Dependant variables parse error: {e}")
            return None

    @__check_offset
    def __parse_calibrationHeader(self: object, offset: int) -> int:
        try:
            calibrationHeaderCountNum_format = 'b'
            calibrationSeries_buffer_format = '<b 20s i h h'
            calibrationHeaderInfo = namedtuple('calibrationHeader', 'calibrationNum calibrationSeries, byteStream byteStreamLength')
            calibrationHeaderCount, = struct.unpack_from(calibrationHeaderCountNum_format, self.__asdFileStream, offset)
            byteStream = self.__asdFileStream[offset:offset + struct.calcsize(calibrationHeaderCountNum_format) + struct.calcsize(calibrationSeries_buffer_format)*calibrationHeaderCount]
            byteStreamLength = len(byteStream)
            offset += struct.calcsize(calibrationHeaderCountNum_format)
            if calibrationHeaderCount > 0:
                calibrationSeries = []
                for i in range(calibrationHeaderCount):
                    (cbtype, cbname, cbIntergrationTime_ms, cbSwir1Gain, cbWwir2Gain) = struct.unpack_from(calibrationSeries_buffer_format, self.__asdFileStream, offset)
                    cbtype_e = CalibrationType_e(cbtype)
                    name = cbname.strip(b'\x00')
                    cbIntergrationTime = IT_ms_e(cbIntergrationTime_ms)
                    calibrationSeries.append(((cbtype_e, name, cbIntergrationTime, cbSwir1Gain, cbWwir2Gain)))
                    offset += struct.calcsize(calibrationSeries_buffer_format)
                self.calibrationHeader = calibrationHeaderInfo._make((calibrationHeaderCount, calibrationSeries, byteStream, byteStreamLength))
            else:
                calibrationSeries = []
                self.calibrationHeader = calibrationHeaderInfo._make((calibrationHeaderCount, calibrationSeries, byteStream, byteStreamLength))
            # logger.info(f"Read: calibration header end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"Calibration Header parse error: {e}")
            return None

    @__check_offset
    def __parse_auditLog(self: object, offset: int) -> int:
        try:
            initOffset = offset
            auditLogInfo = namedtuple('auditLog', 'auditCount auditEvents byteStream byteStreamLength')
            additCount, = struct.unpack_from('l', self.__asdFileStream, offset)
            offset += struct.calcsize('l')
            if additCount > 0:
                offset += 10
                auditEvents, auditEventsLength = self.__parse_auditEvents(offset)
                offset += auditEventsLength
            self.auditLog = auditLogInfo._make((additCount, auditEvents, self.__asdFileStream[initOffset:offset], len(self.__asdFileStream[initOffset:offset])))
            # logger.info(f"Read: audit log header end offset: {offset}")
            return offset
        except Exception as e:
            logger.exception(f"Audit Log Header parse error: {e}")
            return None

    @__check_offset
    def __parse_signature(self: object, offset: int) -> int:
        try:
            initOffset = offset
            signatureInfo = namedtuple('signature', 'signed, signatureTime, userDomain, userLogin, userName, source, reason, notes, publicKey, signature, byteStream, byteStreamLength')
            signed_int, = struct.unpack_from('b', self.__asdFileStream, offset)
            # 0 – Unsigned
            # 1 - Signed
            signed_map = {0: SignatureState_e.UN_SIGNED, 1: SignatureState_e.SIGNED} 
            if signed_int not in signed_map:
                signed = SignatureState_e.SIGNED_INVALID
            # set the file version based on the version string
            else:
                signed = signed_map[signed_int]
            offset += struct.calcsize('b')
            signatureTime_int, = struct.unpack_from('q', self.__asdFileStream, offset)
            #! The timestamp is to be parsed 
            signatureTime = signatureTime_int
            # start_date = datetime(1, 1, 1)
            # signatureTime = start_date + timedelta(seconds=signatureTime_int // 10000000)
            # signatureTime = datetime.fromtimestamp(signatureTime_int, tz=)  # Convert to datetime
            offset += struct.calcsize('q')
            userDomain, offset = self.__parse_bstr(offset)
            userLogin, offset = self.__parse_bstr(offset)
            userName, offset = self.__parse_bstr(offset)
            source, offset = self.__parse_bstr(offset)
            reason, offset = self.__parse_bstr(offset)
            notes, offset = self.__parse_bstr(offset)
            publicKey, offset = self.__parse_bstr(offset)
            # signature, offset = self.__parse_bstr(offset)
            signature, = struct.unpack_from('128s', self.__asdFileStream, offset)
            offset += struct.calcsize('128s')
            byteStream = self.__asdFileStream[initOffset:offset]
            byteStreamLength = len(byteStream)
            self.signature = signatureInfo._make((signed, signatureTime, userDomain, userLogin, userName, source, reason, notes, publicKey, signature, byteStream, byteStreamLength))
            # logger.info(f"Read: signature end offset: {offset}")
        except Exception as e:
            logger.exception(f"Signature parse error: {e}")
            return None
        return offset

    @__check_offset
    def __parse_spectra(self: object, offset: int) -> tuple[np.array, bytes, int, int]:
        try:
            spectra = np.array(struct.unpack_from('<{}d'.format(self.metadata.channels), self.__asdFileStream, offset))
            offset += (self.metadata.channels * 8)
            spectrumDataStream = self.__asdFileStream[offset:offset + self.metadata.channels * 8]
            spectrumDataStreamLength = len(spectrumDataStream)
            return spectra, spectrumDataStream, spectrumDataStreamLength, offset
        except Exception as e:
            logger.exception(f"Spectrum data parse error: {e}")
            return None, None, None, None

    @__check_offset
    def __parse_constituantType(self: object, offset: int) -> tuple[tuple, int]:
        try:
            constituentName, offset = self.__parse_bstr(offset)
            passFail, offset = self.__parse_bstr(offset)
            fmt = '<d d d d d d d d d l d d'
            mDistance, mDistanceLimit, concentration, concentrationLimit, fRatio, residual, residualLimit, scores, scoresLimit, modelType, reserved1, reserved2 = struct.unpack_from(fmt, self.__asdFileStream, offset)
            merterialReportInfo = namedtuple('itemsInMeterialReport', 'constituentName passFail mDistance mDistanceLimit concentration concentrationLimit fRatio residual residualLimit scores scoresLimit modelType reserved1 reserved2')
            itemsInMeterialReport = merterialReportInfo._make((constituentName, passFail, mDistance, mDistanceLimit, concentration, concentrationLimit, fRatio, residual, residualLimit, scores, scoresLimit, modelType, reserved1, reserved2))
            offset += struct.calcsize(fmt)
            # logger.info(f"Read: constituant type end offset: {offset}")
            return itemsInMeterialReport, offset
        except Exception as e:
            logger.exception(f"Constituant Type parse error {e}")
            return None, None

    @__check_offset
    def __parse_bstr(self: object, offset: int) -> tuple[str, int]:
        try:
            size, = struct.unpack_from('<h', self.__asdFileStream, offset)
            offset += struct.calcsize('<h')
            bstr_format = '<{}s'.format(size)
            str = ''
            if size >= 0:
                bstr, = struct.unpack_from(bstr_format, self.__asdFileStream, offset)
                str = bstr.decode('utf-8')
            offset += struct.calcsize(bstr_format)
            return str, offset
        except struct.error as err:
            logger.exception(f"Byte string parse error: {err}")
            return None, None

    @__check_offset
    def __parse_Bool(self: object, offset: int) -> tuple[bool, int]:
        try:
            buffer = self.__asdFileStream[offset:offset + 2]
            if buffer == b'\xFF\xFF':
                return True, offset + 2
            elif buffer == b'\x00\x00':
                return False, offset + 2
            else:
                raise ValueError("Invalid Boolean value")
        except Exception as e:
            return None, None
    
    @__check_offset
    def __parse_auditEvents(self: object, offset: int) -> tuple[list, int]:
        try:
            auditEvents_str = self.__asdFileStream[offset:].decode('utf-8', errors='ignore')
            auditPattern = re.compile(r'<Audit_Event>(.*?)</Audit_Event>', re.DOTALL)
            auditEvents = auditPattern.findall(auditEvents_str)
            auditEvents_list = []
            auditEventLength = 0
            for auditEvent in auditEvents:
                auditEvent = "<Audit_Event>" + auditEvent + "</Audit_Event>"
                auditEventLength += len(auditEvent.encode('utf-8')) + 2
                auditEvents_list.append(auditEvent)
            auditEventsTuple_list = []
            for auditEvent in auditEvents_list:
                auditEventtuple = self.__parse_auditLogEvent(auditEvent)
                auditEventsTuple_list.append(auditEventtuple)
            return auditEventsTuple_list, auditEventLength
        except Exception as e:
            logger.exception(f"Audit Event parse error: {e}")
            return None, None

    def __parse_auditLogEvent(self: object, event: str) -> tuple:
        try:
            auditInfo = namedtuple('event', 'application appVersion name login time source function notes')
            # Security note: xml.etree.ElementTree in Python 3.9+ has XXE protection by default
            # External entities and DTD processing are disabled automatically
            root = ET.fromstring(event)
            application = root.find('Audit_Application').text
            appVersion = root.find('Audit_AppVersion').text
            name = root.find('Audit_Name').text
            login = root.find('Audit_Login').text
            time = root.find('Audit_Time').text
            source = root.find('Audit_Source').text
            function = root.find('Audit_Function').text
            notes = root.find('Audit_Notes').text
            auditEvents = auditInfo._make((application, appVersion, name, login, time, source, function, notes))
            return auditEvents
        except Exception as e:
            logger.exception(f"Audit Log Data parse error: {e}")
            return None

    def __validate_fileVersion(self: object) -> int:
        try:
            # read the file version from the first 3 bytes of the file
            version_data = self.__asdFileStream[:3]
            version_map = {b'ASD': FileVersion_e.FILE_VERSION_1, b'as2': FileVersion_e.FILE_VERSION_2, b'as3': FileVersion_e.FILE_VERSION_3, b'as4': FileVersion_e.FILE_VERSION_4, b'as5': FileVersion_e.FILE_VERSION_5, b'as6': FileVersion_e.FILE_VERSION_6, b'as7': FileVersion_e.FILE_VERSION_7, b'as8': FileVersion_e.FILE_VERSION_8} 
            if version_data not in version_map:
                fileversion = FileVersion_e.FILE_VERSION_INVALID
            # set the file version based on the version string
            else:
                fileversion = version_map[version_data]
            # logger.info(f"File Version: {fileversion}")
            return fileversion, 3
        except Exception as e:
            logger.exception(f"File Version Validation Error:\n{e}")
            return FileVersion_e.FILE_VERSION_INVALID, 3

    def __parseVersion(self, version: int) -> str:
        major = (version & 0xF0) >> 4
        minor = version & 0x0F
        return f"{major}.{minor}"

    # Parse the storage time through 9 short integers and store it as a datetime type
    def __parse_ASDFilewhen(self: object, when: bytes) -> tuple:
        seconds = when[0]               # seconds [0,61]
        minutes = when[1]               # minutes [0,59]
        hour = when[2]                  # hour [0,23]
        day = when[3]                   # day of the month [1,31]
        month = when[4]                 # month of year [0,11]
        year = when[5]                  # years since 1900
        weekDay = when[6]               # day of week [0,6] (Sunday = 0)
        daysInYear = when[7]            # day of year [0,365]
        daylighSavingsFlag = when[8]    # daylight savings flag
        if year < 1900:
            year = year + 1900
        date_datetime = datetime(year, month + 1, day, hour, minutes, seconds)
        return date_datetime, daylighSavingsFlag
    
    def __parse_gps(self: object, gps_field: bytes) -> tuple:
        # Domumentation: ASD File Format Version 8, page 4
        gpsDataInfo = namedtuple('gpsdata', 'trueHeading, speed, latitude, longitude, altitude, lock, hardwareMode, ss, mm, hh, flags1, flags2, satellites, filler1, filler2')
        try:
            gpsDatadFormat = '<d d d d d h b b b b b h 5s b b'
            trueHeading, speed, latitude, longitude, altitude, lock, hardwareMode, ss, mm, hh, flags1, flags2, satellites, filler1, filler2 = struct.unpack(gpsDatadFormat, gps_field)
            gpsData = gpsDataInfo._make((trueHeading, speed, latitude, longitude, altitude, lock, hardwareMode, ss, mm, hh, flags1, flags2, satellites, filler1, filler2))
            return gpsData
        except Exception as e:
            logger.exception(f"GPS parse error: {e}")
            return None

    def __parse_SmartDetector(self: object, smartDetectorData: bytes) -> tuple:
        try:
            smartDetectorFormat = '<i f f f h b f f'
            smartDetectorInfo = namedtuple('smartDetector', 'serialNumber signal dark ref status avg humid temp')
            serialNumber, signal, dark, ref, status, avg, humid, temp = struct.unpack(smartDetectorFormat, smartDetectorData)
            smartDetector = smartDetectorInfo._make((serialNumber, signal, dark, ref, status, avg, humid, temp))
            return smartDetector
        except Exception as e:
            logger.exception(f"Smart Detector parse error: {e}")
            return None
    
    def __parseSaturationError(self, flags2: int) -> list:
        errors = []
        if flags2 & 0x01:
            errors.append(SaturationError_e.VNIR_SATURATION)
        if flags2 & 0x02:
            errors.append(SaturationError_e.SWIR1_SATURATION)
        if flags2 & 0x04:
            errors.append(SaturationError_e.SWIR2_SATURATION)
        if flags2 & 0x08:
            errors.append(SaturationError_e.SWIR1_TEC_ALARM)
        if flags2 & 0x10:  # Fixed: was 0x16 (22), should be 0x10 (16)
            errors.append(SaturationError_e.SWIR2_TEC_ALARM)
        return errors

    def __parseTimeOLE(self: object, timeole: float) -> datetime:
        try:
            ole_base_date = datetime(1899, 12, 30)
            days = int(timeole)
            fraction = timeole - days
            total_hours = fraction * 24
            hours = int(total_hours)
            minutes = int((total_hours - hours) * 60)
            seconds = int(((total_hours - hours) * 60 - minutes) * 60)
            microseconds = int((((total_hours - hours) * 60 - minutes) * 60 - seconds) * 1000000)
            time_delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
            result_datetime = ole_base_date + time_delta
            return result_datetime
        except Exception as e:
            logger.exception(f"OLE time parse error: {e}")
            return None

    #! Need to check the result of the function
    @property
    def digitalNumber(self):
        return self.spectrumData.spectra if self.spectrumData is not None else None

    @property
    def whiteReference(self):
        if self.referenceData is not None:
            return self.__normalise_spectrum(self.referenceData.spectra)
        else:
            return None

    @property
    def reflectance(self):
        if self.metadata.asdFileVersion.value >= 2:
            try:
                if self.metadata.referenceTime and self.metadata.dataType == DataType_e.dt_REF_TYPE:
                    reflectance = np.divide(self.__normalise_spectrum(self.spectrumData.spectra), self.__normalise_spectrum(self.referenceData.spectra), where=self.__normalise_spectrum(self.referenceData.spectra) != 0)
                    return reflectance
                else:
                    return None
            except Exception as e:
                logger.info(f"Reflectance calculation error: {e}")
                return None
        else:
            logger.info("Reflectance calculation error: Unsupported file version")
            return None

    @property
    def reflectanceNoDeriv(self):
        return self.reflectance

    @property
    def reflectance1stDeriv(self):
        if self.reflectance is not None:
            return self.__derivative(self.reflectance)
        else:
            return None

    @property
    def reflectance2ndDeriv(self):
        if self.reflectance1stDeriv is not None:
            return self.__derivative(self.reflectance1stDeriv)
        else:
            return None

    #* Need to check the result of the function, not available in the SpecView
    # 3rd Derivative
    @property
    def reflectance3rdDeriv(self):
        if self.reflectance2ndDeriv is not None:
            return self.__derivative(self.reflectance2ndDeriv)
        else:
            return None

    #! Need to check the result of the function
    # Reflectance (Transmittance)
    @property
    def transmitance(self):
        pass

    def __normalise_spectrum(self: object, spectrum) -> np.array:
        # normalise the spectrum data, for VNIR and SWIR1, SWIR2, the data is normalised based on the integration time and gain
        if spectrum is not None:
            spectra = np.array(spectrum)
            splice1_index = int(self.metadata.splice1_wavelength)
            splice2_index = int(self.metadata.splice2_wavelength)
            spectra[:splice1_index] = spectra[:splice1_index] / self.metadata.intergrationTime_ms.value
            # 
            spectra[splice1_index:splice2_index] = spectra[splice1_index:splice2_index] * self.metadata.swir1Gain / 2048
            spectra[splice2_index:] = spectra[splice2_index:] * self.metadata.swir2Gain / 2048
            return spectra
        else:
            return None

    def __derivative(self, data: np.array) -> np.array:
        derivative = np.zeros_like(data)
        D1 = ASDFile.DEFAULT_DERIVATIVE_GAP // 2
        D2 = ASDFile.DEFAULT_DERIVATIVE_GAP - 1
        derivative[D1:-D1] = (data[D1*2:] - data[:-D1*2]) / D2
        # for i in range(D1, len(data) - D1):
        #     derivative[i] = (data[i + D1] - data[i - D1]) / D2
        return derivative

    @property
    def absoluteReflectance(self):
        if self.calibrationSeriesABS is not None:
            return np.multiply(self.reflectance, self.calibrationSeriesABS)
        else:
            return None

    @property
    def log1R(self):
        if self.reflectance is not None:
            return np.log(1/self.reflectance)/np.log(10)
        else:
            return None

    #! Need to check the result of the function
    @property
    def log1T(self):
        pass

    @property
    def log1RNoDeriv(self):
        if self.log1R is not None:
            return self.log1R
        else:
            return None

    @property
    def log1R1stDeriv(self):
        if self.log1R is not None:
            return self.__derivative(self.log1R)
        else:
            return None

    @property
    def log1R2ndDeriv(self):
        if self.log1R1stDeriv is not None:
            return self.__derivative(self.log1R1stDeriv)
        else:
            return None


    #! Need to check the result of the function
    @property
    def radiance(self, pcc: bool = False):
        if self.calibrationHeader is not None:
            if self.calibrationHeader.calibrationNum >= 3 and (all(x is not None for x in [self.calibrationSeriesABS, self.calibrationSeriesLMP, self.calibrationSeriesBSE]) or all(x is not None for x in [self.calibrationSeriesBSE, self.calibrationSeriesLMP, self.calibrationSeriesFO])):
                for i in range(self.calibrationHeader.calibrationNum):
                    if self.calibrationHeader.calibrationSeries[i][0] == CalibrationType_e.cb_FIBER:
                        responseCal_info = namedtuple('responseCal', 'cbIT cbS1Gain cbS2Gain')
                        cbIT, cbS1Gain, cbS2Gain = self.calibrationHeader.calibrationSeries[i][2:5]
                        responseCal = responseCal_info._make((cbIT, cbS1Gain, cbS2Gain))
                if self.metadata.fo >= 180:
                    radiance = self.__calc_irradiance(responseCal)
                else:
                    radiance = self.__calc_radiance(responseCal)
                if pcc == True:
                    radiance = self.__parabolic_correction(radiance)
            else:
                logger.info("Radiance calculation error: Invalid calibration header data")
                return None
            return radiance
        else:
            logger.info("Radiance calculation error: Invalid calibration header data")
            return None

    def __calc_radiance(self, response_cal) -> np.ndarray:
        radiance = self.__calc_irradiance(response_cal)
        radiance *= (self.calibrationSeriesBSE / np.pi)
        return radiance

    def __calc_irradiance(self, responseCal) -> np.ndarray:
        DEFAULT_GAIN = 2048.0
        radiance = np.zeros(self.metadata.channels)
        dVnirConstant = 0.0
        dSwir1Constant = 0.0
        dSwir2Constant = 0.0
        dSplice1 = 0.0
        dSplice2 = 0.0
        # Determine the last wavelength
        dLastWavelength = self.metadata.channel1Wavelength + (self.metadata.channels - 1) * self.metadata.wavelengthStep
        # Set the Splice Points
        instrument = self.metadata.instrument
        if instrument in [InstrumentType_e.UNKNOWN_INSTRUMENT, InstrumentType_e.PSII_INSTRUMENT, InstrumentType_e.LSVNIR_INSTRUMENT, InstrumentType_e.FSVNIR_INSTRUMENT, InstrumentType_e.HAND_HELD_INSTRUMENT]:
            dSplice1 = dLastWavelength
            dSplice2 = dLastWavelength
        elif instrument == InstrumentType_e.FSFR_INSTRUMENT:
            dSplice1 = self.metadata.splice1_wavelength
            dSplice2 = self.metadata.splice2_wavelength
        elif instrument == InstrumentType_e.FSNIR_INSTRUMENT:
            dSplice1 = self.metadata.channel1Wavelength
            dSplice2 = self.metadata.splice2_wavelength
        # Set the Starting Wavelength
        dWavelength = self.metadata.channel1Wavelength
        i = 0
        if instrument != InstrumentType_e.FSNIR_INSTRUMENT:
            # VNIR
            dVnirConstant = float(responseCal.cbIT.value) / float(self.metadata.intergrationTime_ms.value)
            while dWavelength <= dSplice1 and i < self.metadata.channels:
                if self.calibrationSeriesFO[i] != 0:
                    radiance[i] = float(self.calibrationSeriesLMP[i]) * (float(self.spectrumData.spectra[i]) / float(self.calibrationSeriesFO[i])) * dVnirConstant
                else:
                    radiance[i] = 0
                i += 1
                dWavelength += self.metadata.wavelengthStep
        if instrument in [InstrumentType_e.FSFR_INSTRUMENT, InstrumentType_e.FSNIR_INSTRUMENT]:
            # SWiR1
            dSwir1Constant = ((DEFAULT_GAIN / responseCal.cbS1Gain) / (DEFAULT_GAIN / self.metadata.swir1Gain))
            while dWavelength <= dSplice2 and i < self.metadata.channels:
                if self.calibrationSeriesFO[i] != 0:
                    radiance[i] = self.calibrationSeriesLMP[i] * (self.spectrumData.spectra[i] / self.calibrationSeriesFO[i]) * dSwir1Constant
                else:
                    radiance[i] = 0
                i += 1
                dWavelength += self.metadata.wavelengthStep
            # SWiR2
            dSwir2Constant = ((DEFAULT_GAIN / responseCal.cbS2Gain) / (DEFAULT_GAIN / self.metadata.swir2Gain))
            while dWavelength <= dLastWavelength and i < self.metadata.channels:
                if self.calibrationSeriesFO[i] != 0:
                    radiance[i] = self.calibrationSeriesLMP[i] * (self.spectrumData.spectra[i] / self.calibrationSeriesFO[i]) * dSwir2Constant
                else:
                    radiance[i] = 0
                i += 1
                dWavelength += self.metadata.wavelengthStep
        return radiance

    #! Need to check the result of the function
    def __parabolic_correction(self, radiance: np.ndarray) -> np.ndarray:

        DEFAULT_GAP = 3
        iAvgLen = 0
        iIndex = 0
        dPC = 0.0

        iStartingWavelength = int(self.metadata.channel1_wavelength)
        iEndingWavelength = int(self.metadata.channels - 1) + int(self.metadata.channel1_wavelength)

        InstrumentType = self.get_instrument_type(iStartingWavelength, iEndingWavelength)

        iSplice1 = int(self.metadata.splice1_wavelength)
        iSplice2 = int(self.metadata.splice2_wavelength)
        iVertex1 = 675
        iVertex2 = 1975

        if (((InstrumentType & InstrumentModel_e.itVnir.value) == InstrumentModel_e.itVnir.value) and
            ((InstrumentType & InstrumentModel_e.itSwir1.value) == InstrumentModel_e.itSwir1.value) and
            ((InstrumentType & InstrumentModel_e.itSwir2.value) == InstrumentModel_e.itSwir2.value)) or \
           (((InstrumentType & InstrumentModel_e.itVnir.value) == InstrumentModel_e.itVnir.value) and
            ((InstrumentType & InstrumentModel_e.itSwir1.value) == InstrumentModel_e.itSwir1.value)) or \
           (((InstrumentType & InstrumentModel_e.itSwir1.value) == InstrumentModel_e.itSwir1.value) and
            ((InstrumentType & InstrumentModel_e.itSwir2.value) == InstrumentModel_e.itSwir2.value)):

            iAvgLen = iSplice1 - iVertex1
            iIndex = iSplice1 - iStartingWavelength
            # 计算 VNIR 或 SWIR1 的 pfactor
            dPC = radiance[iIndex]

            if dPC == 0:
                dPC = 1

            dPCFactor1 = (self.average(radiance, iIndex + 1, DEFAULT_GAP) - radiance[iIndex]) / (dPC * iAvgLen * iAvgLen)

            nPoint = abs(iVertex1 - iStartingWavelength)
            iWavelength = iVertex1
            dE = len(radiance)

            while iWavelength <= iSplice1:
                if nPoint <= dE:
                    radiance[nPoint] *= (dPCFactor1 * (iWavelength - iVertex1) ** 2 + 1)
                nPoint += 1
                iWavelength += 1

            if InstrumentType == InstrumentModel_e.itVnirSwir1Swir2.value:
                # 计算 SWIR2 的 PC
                iAvgLen = iSplice2 - iVertex2

                iIndex = iSplice2 - iStartingWavelength
                # 计算 SWIR2 的 pfactor
                dPC = self.average(radiance, iIndex + 1, DEFAULT_GAP)

                if dPC == 0:
                    dPC = 1

                dPCFactor2 = (self.average(radiance, iIndex - 2, DEFAULT_GAP) -
                              self.average(radiance, iIndex + 1, DEFAULT_GAP)) / (dPC * iAvgLen * iAvgLen)

                nPoint = (iSplice2 - iStartingWavelength) + 1
                iWavelength = iSplice2 + 1

                while iWavelength <= iVertex2:
                    radiance[nPoint] *= (dPCFactor2 * (iWavelength - iVertex2) ** 2 + 1)
                    nPoint += 1
                    iWavelength += 1

        return radiance
        
# TODO: Implement the following functions
# Radiometric Calculation
# Parabolic Correction
# Splice Correction
# Lambda Integration
# Quantum lntensity
# Interpolate
# Statistics
# NEDL
# ASCll Export
# Import Ascii X,Y
# JCAMP-DX Export
# Bran+Luebbe
# Colorimetry..
# GPS Log
# Convex Hull
# Custom...

