const DIRECTION_UNKNOWN = 0;
const DIRECTION_AXIAL = 1;
const DIRECTION_CORONAL = 2;
const DIRECTION_SAGITTAL = 3;
const DIRECTION_TEMPORAL = 4;
const DIRECTION_SURFACE = 5;
const DIRECTION_CURVED = 6;
onmessage = function (msg) {
    // worker received message from main thread
    // console.log('worker received this', msg.data);
    // const returnPayload = {
    //     pixelData: msg.data.imageData.data[msg.data.index],
    //     msg: 'worker say hi to main thread',
    //     index: msg.data.index
    // };
    // const imageSegment = getImageSegment(msg.data);
    getImageSegment(msg.data);
    // const imageSegment = convertToPapayaImage(getImageSegment(msg.data));
    // console.log('imageSegment', imageSegment);
    postMessage({
        sliceProps: msg.data.sliceProps
    });
};
// const convertToPapayaImage = function (inputImage) {
//     // rearrange image to match with Papaya Image data
//     const image = [];
//     for (let i = 0; i < inputImage.length; i++) {
//         image[i * 4] = inputImage[i];
//     }
//     return image;
// };

const getImageSegment = function (data) {
    const { xDim, yDim, xSegments, ySegments, sliceDirection, xSize, ySize, zSize, slice, scaleFactor = 1 } = data.sliceProps;
    // console.log('getImageSegment', xDim, yDim, ySegments, data.mat);
    // console.log('getImageSegment data', data);
    const imageSegment = [];
    let value = 0;
    let index;
    // let debugImageLength = 0;
    // const debugIndexesSet = new Set();
    // const debugIndexes = [];
    const stepping = 1 / scaleFactor;
    // console.log('stepping', stepping);
    for (let y = ySegments[0]; y < ySegments[1]; y += stepping) {
        for (let x = 0; x < xDim; x += stepping) {
        // for (let y = 0; y < yDim; y += stepping) {
        //     for (let x = xSegments[0]; x < xSegments[1]; x += stepping) {
            if (sliceDirection === DIRECTION_AXIAL) {
                value = getVoxelAtMM(x * xSize, y *
                    ySize, slice * zSize, data);
                // if (y < 2) debugIndexes.push([x * xSize, y * ySize]);
            } else if (sliceDirection === DIRECTION_CORONAL) {
                value = getVoxelAtMM(x * xSize, slice *
                    ySize, y * zSize, data);
            } else if (sliceDirection === DIRECTION_SAGITTAL) {
                value = getVoxelAtMM(slice * xSize, x *
                    ySize, y * zSize, data);
            }
            index = ((papayaRoundFast(y * scaleFactor) * papayaRoundFast(xDim * scaleFactor)) + papayaRoundFast(x * scaleFactor)) * 4;
            // debugIndexes.push(index);
            // debugIndexesSet.add(index);
            data.sliceProps.imageData[index] = value;
            // debugImageLength++;
            // imageSegment.push(value);
        }
    }
    // console.log('index', debugIndexes);
    // console.log('Image length', debugImageLength);
    // console.log('expected xDim', xDim * scaleFactor);
    // console.log('actual xDim', debugImageLength / (yDim * scaleFactor));
    // console.log('expected yDim', yDim * scaleFactor);
    // console.log('actual yDim', debugImageLength / (xDim * scaleFactor));
    // console.log('indexes length', debugIndexes.length);
    // console.log('unique indexes length', debugIndexesSet.size);
    return imageSegment;
};

const getVoxelAtMM = function (xLoc, yLoc, zLoc, data) {
    const mat = data.mat;
    const xTrans = ((xLoc * mat[0][0]) + (yLoc * mat[0][1]) + (zLoc * mat[0][2]) + (mat[0][3]));
    const yTrans = ((xLoc * mat[1][0]) + (yLoc * mat[1][1]) + (zLoc * mat[1][2]) + (mat[1][3]));
    const zTrans = ((xLoc * mat[2][0]) + (yLoc * mat[2][1]) + (zLoc * mat[2][2]) + (mat[2][3]));
    return getVoxelAtIndexNative(xTrans, yTrans, zTrans, data);
};

const getVoxelAtIndexNative = function (xTrans, yTrans, zTrans, data) {
    if (!data.sliceProps.interpolation) {
        const xRound = papayaRoundFast(xTrans);
        const yRound = papayaRoundFast(yTrans);
        const zRound = papayaRoundFast(zTrans);

        return getVoxelAtOffset(
            convertIndexToOffsetNative(xRound,
                yRound,
                zRound,
                data), xRound, yRound, zRound, data
        );
    }

    return getVoxelAtIndexLinear(xTrans, yTrans, zTrans, data);
};

const convertIndexToOffsetNative = function (xLoc, yLoc, zLoc, data) {
    const { xIncrement, yIncrement, zIncrement } = data.stackProps;
    return (xLoc * xIncrement) + (yLoc * yIncrement) + (zLoc * zIncrement);
};

const getVoxelAtOffset = function (volOffset, xLoc, yLoc, zLoc, data) {
    // console.log(data);
    const { timepoint } = data.sliceProps;
    const { volSize,
        stackXDim,
        stackYDim,
        stackZDim,
        imageData,
        usesGlobalDataScale,
        globalDataScaleSlope,
        globalDataScaleIntercept,
        sliceSize,
        dataScaleSlopes,
        dataScaleIntercepts,
        forceABS
    } = data.stackProps;
    let dataScaleIndex;
    const offset = volOffset + (volSize * timepoint);
    let value;

    if ((xLoc < 0) || (xLoc >= stackXDim) || (yLoc < 0) || (yLoc >= stackYDim) || (zLoc < 0) || (zLoc >= stackZDim)) {
        return 0;
    }
    if (usesGlobalDataScale) {
        value = (checkSwap(imageData.data[offset], data) * globalDataScaleSlope) +
            globalDataScaleIntercept;
    } else {
        dataScaleIndex = parseInt(offset / sliceSize);
        value = (checkSwap(imageData.data[offset], data) * dataScaleSlopes[dataScaleIndex]) +
        dataScaleIntercepts[dataScaleIndex];
    }

    if (forceABS) {
        return Math.abs(value);
    }
    return value;
};

const checkSwap = function (val, data) {
    const { swap16, swap32 } = data.stackProps;
    if (swap16) {
        return ((((val & 0xFF) << 8) | ((val >> 8) & 0xFF)) << 16) >> 16; // since JS uses 32-bit  when bit shifting
    }

    if (swap32) {
        return ((val & 0xFF) << 24) | ((val & 0xFF00) << 8) | ((val >> 8) & 0xFF00) | ((val >> 24) & 0xFF);
    }

    return val;
};

// const getVoxelAtIndexLinear = function () {
//     return -1;
// };

const getVoxelAtIndexLinear = function (xLoc, yLoc, zLoc, data) {
    const { timepoint } = data.sliceProps;
    let offset;
    let value = 0;
    let tempVal1 = 0;
    let tempVal2 = 0;
    const xInt = Math.floor(xLoc);
    const yInt = Math.floor(yLoc);
    const zInt = Math.floor(zLoc);

    const fracX = xLoc - xInt;
    const fracY = yLoc - yInt;
    const fracZ = zLoc - zInt;

    const interpolateX = (fracX !== 0);
    const interpolateY = (fracY !== 0);
    const interpolateZ = (fracZ !== 0);

    const interpFirstPass = [[0, 0], [0, 0]];
    const interpSecondPass = [0, 0];

    if (interpolateX && interpolateY && interpolateZ) {
        for (let x = 0; x < 2; x++) {
            for (let y = 0; y < 2; y++) {
                offset = convertIndexToOffsetNative(xInt + x, yInt + y, zInt, data);
                tempVal1 = getVoxelAtOffset(offset, xInt + x, yInt + y, zInt, data) * (1 - fracZ);
                offset = convertIndexToOffsetNative(xInt + x, yInt + y, zInt + 1, data);
                tempVal2 = getVoxelAtOffset(offset, xInt + x, yInt + y, zInt + 1, data) * fracZ;
                interpFirstPass[x][y] = tempVal1 + tempVal2;
            }
        }

        interpSecondPass[0] = (interpFirstPass[0][0] * (1 - fracY)) + (interpFirstPass[0][1] * fracY);
        interpSecondPass[1] = (interpFirstPass[1][0] * (1 - fracY)) + (interpFirstPass[1][1] * fracY);

        value = (interpSecondPass[0] * (1 - fracX)) + (interpSecondPass[1] * fracX);
    } else if (interpolateX && interpolateY && !interpolateZ) {
        for (let x = 0; x < 2; x++) {
            offset = convertIndexToOffsetNative(xInt + x, yInt, zInt, data);
            tempVal1 = getVoxelAtOffset(offset, xInt + x, yInt, zInt, data) * (1 - fracY);
            offset = convertIndexToOffsetNative(xInt + x, yInt + 1, zInt, data);
            tempVal2 = getVoxelAtOffset(offset, xInt + x, yInt + 1, zInt, data) * fracY;
            interpSecondPass[x] = tempVal1 + tempVal2;
        }

        value = (interpSecondPass[0] * (1 - fracX)) + (interpSecondPass[1] * fracX);
    } else if (interpolateX && !interpolateY && interpolateZ) {
        for (let x = 0; x < 2; x++) {
            offset = convertIndexToOffsetNative(xInt + x, yInt, zInt, data);
            tempVal1 = getVoxelAtOffset(offset, xInt + x, yInt, zInt, data) * (1 - fracZ);
            offset = convertIndexToOffsetNative(xInt + x, yInt, zInt + 1, data);
            tempVal2 = getVoxelAtOffset(offset, xInt + x, yInt, zInt + 1, data) * fracZ;
            interpSecondPass[x] = tempVal1 + tempVal2;
        }

        value = (interpSecondPass[0] * (1 - fracX)) + (interpSecondPass[1] * fracX);
    } else if (!interpolateX && interpolateY && interpolateZ) {
        for (let y = 0; y < 2; y++) {
            offset = convertIndexToOffsetNative(xInt, yInt + y, zInt, data);
            tempVal1 = getVoxelAtOffset(offset, xInt, yInt + y, zInt, data) * (1 - fracZ);
            offset = convertIndexToOffsetNative(xInt, yInt + y, zInt + 1, data);
            tempVal2 = getVoxelAtOffset(offset, xInt, yInt + y, zInt + 1, data) * fracZ;
            interpSecondPass[y] = tempVal1 + tempVal2;
        }

        value = (interpSecondPass[0] * (1 - fracY)) + (interpSecondPass[1] * fracY);
    } else if (!interpolateX && !interpolateY && interpolateZ) {
        offset = convertIndexToOffsetNative(xInt, yInt, zInt, data);
        tempVal1 = getVoxelAtOffset(offset, xInt, yInt, zInt, data) * (1 - fracZ);
        offset = convertIndexToOffsetNative(xInt, yInt, zInt + 1, data);
        tempVal2 = getVoxelAtOffset(offset, xInt, yInt, zInt + 1, data) * fracZ;
        value = tempVal1 + tempVal2;
    } else if (!interpolateX && interpolateY && !interpolateZ) {
        offset = convertIndexToOffsetNative(xInt, yInt, zInt, data);
        tempVal1 = getVoxelAtOffset(offset, xInt, yInt, zInt, data) * (1 - fracY);
        offset = convertIndexToOffsetNative(xInt, yInt + 1, zInt, data);
        tempVal2 = getVoxelAtOffset(offset, xInt, yInt + 1, zInt, data) * fracY;
        value = tempVal1 + tempVal2;
    } else if (interpolateX && !interpolateY && !interpolateZ) {
        offset = convertIndexToOffsetNative(xInt, yInt, zInt, data);
        tempVal1 = getVoxelAtOffset(offset, xInt, yInt, zInt, data) * (1 - fracX);
        offset = convertIndexToOffsetNative(xInt + 1, yInt, zInt, data);
        tempVal2 = getVoxelAtOffset(offset, xInt + 1, yInt, zInt, data) * fracX;
        value = tempVal1 + tempVal2;
    } else { // if(!interpolateX && !interpolateY && !interpolateZ)
        value = getVoxelAtOffset(convertIndexToOffsetNative(xLoc, yLoc, zLoc, data), xLoc, yLoc, zLoc, data);
    }

    return value;
};

const papayaRoundFast = function (val) {
    if (val > 0) {
        return (val + 0.5) | 0;
    }

    return (val - 0.5) | 0;
};
