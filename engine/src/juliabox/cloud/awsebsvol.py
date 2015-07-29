__author__ = 'tan'
# import datetime
import time
import os
# import sh
# import stat
# import pytz

from juliabox.cloud.aws import CloudHost
from juliabox.jbox_util import retry, create_host_mnt_command
# from juliabox.jbox_util import parse_iso_time


class EBSVol(CloudHost):
    SH_MOUNT = None
    SH_UMOUNT = None
    SH_LIST_DIR = None

    # @staticmethod
    # def _get_block_device_mapping(instance_id):
    #     maps = CloudHost.connect_ec2().get_instance_attribute(instance_id=instance_id,
    #                                                           attribute='blockDeviceMapping')['blockDeviceMapping']
    #     idmap = {}
    #     for dev_path, dev in maps.iteritems():
    #         idmap[dev_path] = dev.volume_id
    #     return idmap

    @staticmethod
    def configure_host_commands():
        if EBSVol.SH_LIST_DIR is None:
            EBSVol.SH_LIST_DIR = create_host_mnt_command("ls -la")
        if EBSVol.SH_MOUNT is None:
            EBSVol.SH_MOUNT = create_host_mnt_command("mount")
        if EBSVol.SH_UMOUNT is None:
            EBSVol.SH_UMOUNT = create_host_mnt_command("umount")

    # @staticmethod
    # def _mount_device(dev_id, mount_dir):
    #     EBSVol.configure_host_commands()
    #     t1 = time.time()
    #     device = os.path.join('/dev', dev_id)
    #     mount_point = os.path.join(mount_dir, dev_id)
    #     actual_mount_point = EBSVol._get_mount_point(dev_id)
    #     if actual_mount_point == mount_point:
    #         EBSVol.log_debug("Device %s already mounted at %s", device, mount_point)
    #         return
    #     elif actual_mount_point is None:
    #         EBSVol.log_debug("Mounting device %s at %s", device, mount_point)
    #         res = EBSVol.SH_MOUNT(mount_point)  # the mount point must be mentioned in fstab file
    #         if res.exit_code != 0:
    #             raise Exception("Failed to mount device %s at %s. Error code: %d", device, mount_point, res.exit_code)
    #     else:
    #         raise Exception("Device already mounted at " + actual_mount_point)
    #     tdiff = int(time.time() - t1)
    #     EBSVol.publish_stats("EBSMountTime", "Count", tdiff)

    @staticmethod
    def get_volume(vol_id):
        vols = CloudHost.connect_ec2().get_all_volumes([vol_id])
        if len(vols) == 0:
            return None
        return vols[0]

    @staticmethod
    def _get_volume_attach_info(vol_id):
        vol = EBSVol.get_volume(vol_id)
        if vol is None:
            return None, None
        att = vol.attach_data
        return att.instance_id, att.device

    # @staticmethod
    # def unmount_device(dev_id, mount_dir):
    #     EBSVol.configure_host_commands()
    #     mount_point = os.path.join(mount_dir, dev_id)
    #     actual_mount_point = EBSVol._get_mount_point(dev_id)
    #     if actual_mount_point is None:
    #         return  # not mounted
    #     t1 = time.time()
    #     if mount_point != actual_mount_point:
    #         EBSVol.log_warn("Mount point expected: %s, actual: %r. Taking actual.", mount_point, actual_mount_point)
    #         mount_point = actual_mount_point
    #     EBSVol.log_debug("Unmounting dev_id: %r from %r", dev_id, mount_point)
    #     res = EBSVol.SH_UMOUNT(mount_point)  # the mount point must be mentioned in fstab file
    #     if res.exit_code != 0:
    #         raise Exception("Device could not be unmounted from " + mount_point)
    #     tdiff = int(time.time() - t1)
    #     EBSVol.publish_stats("EBSUnmountTime", "Count", tdiff)

    # @staticmethod
    # def _get_mount_point(dev_id):
    #     EBSVol.configure_host_commands()
    #     device = os.path.join('/dev', dev_id)
    #     for line in EBSVol.SH_MOUNT():
    #         if line.startswith(device):
    #             return line.split()[2]
    #     return None

    @staticmethod
    def _device_exists(dev):
        try:
            line = EBSVol.SH_LIST_DIR(dev)
            line = str(line)
            # look for b indicating block device.
            # use stat instead?
            return len(line) > 0 and line[0] == 'b'
        except:
            # EBSVol.log_exception("Exception waiting for device state")
            return False

    # @staticmethod
    # def _device_exists(dev):
    #     try:
    #         mode = os.stat(dev).st_mode
    #     except OSError:
    #         return False
    #     return stat.S_ISBLK(mode)

    @staticmethod
    @retry(6, 1, backoff=2)
    def _wait_for_device(dev):
        return EBSVol._device_exists(dev)

    @staticmethod
    def _ensure_volume_available(vol_id, force_detach=False):
        conn = CloudHost.connect_ec2()
        vol = EBSVol.get_volume(vol_id)
        if vol is None:
            raise Exception("Volume not found: " + vol_id)

        if CloudHost._state_check(vol, 'available'):
            return True

        # volume may be attached
        instance_id = CloudHost.instance_id()
        att_instance_id, att_device = EBSVol._get_volume_attach_info(vol_id)

        if (att_instance_id is None) or (att_instance_id == instance_id):
            return True

        if force_detach:
            EBSVol.log_warn("Forcing detach of volume %s", vol_id)
            conn.detach_volume(vol_id)
            CloudHost._wait_for_status(vol, 'available')

        if not CloudHost._state_check(vol, 'available'):
            raise Exception("Volume not available: " + vol_id +
                            ", attached to: " + att_instance_id +
                            ", state: " + vol.status)

    @staticmethod
    def _attach_free_volume(vol_id, dev_id):
        conn = CloudHost.connect_ec2()
        instance_id = CloudHost.instance_id()
        device = os.path.join('/dev', dev_id)
        vol = EBSVol.get_volume(vol_id)

        EBSVol.log_info("Attaching volume %s at %s", vol_id, device)
        t1 = time.time()
        conn.attach_volume(vol_id, instance_id, device)

        if not CloudHost._wait_for_status(vol, 'in-use'):
            EBSVol.log_error("Could not attach volume %s", vol_id)
            raise Exception("Volume could not be attached. Volume id: " + vol_id)

        if not EBSVol._wait_for_device(device):
            EBSVol.log_error("Could not attach volume %s to device %s", vol_id, device)
            raise Exception("Volume could not be attached. Volume id: " + vol_id + ", device: " + device)
        tdiff = int(time.time() - t1)
        CloudHost.publish_stats("EBSAttachTime", "Count", tdiff)

        return device

    @staticmethod
    def get_mapped_volumes(instance_id=None):
        if instance_id is None:
            instance_id = CloudHost.instance_id()

        return CloudHost.connect_ec2().get_instance_attribute(instance_id=instance_id,
                                                              attribute='blockDeviceMapping')['blockDeviceMapping']

    @staticmethod
    def get_volume_id_from_device(dev_id):
        device = os.path.join('/dev', dev_id)
        maps = EBSVol.get_mapped_volumes()
        EBSVol.log_debug("Devices mapped: %r", maps)
        if device not in maps:
            return None
        return maps[device].volume_id

    @staticmethod
    def is_snapshot_complete(snap_id):
        snaps = CloudHost.connect_ec2().get_all_snapshots([snap_id])
        if len(snaps) == 0:
            raise Exception("Snapshot not found with id " + str(snap_id))
        snap = snaps[0]
        return snap.status == 'completed'

    # @staticmethod
    # def get_snapshot_age(snap_id):
    #     snaps = CloudHost.connect_ec2().get_all_snapshots([snap_id])
    #     if len(snaps) == 0:
    #         raise Exception("Snapshot not found with id " + str(snap_id))
    #     snap = snaps[0]
    #
    #     st = parse_iso_time(snap.start_time)
    #     nt = datetime.datetime.now(pytz.utc)
    #     return nt - st

    @staticmethod
    def create_new_volume(snap_id, dev_id, tag=None, disk_sz_gb=1):
        EBSVol.configure_host_commands()
        EBSVol.log_info("Creating volume. Tag: %s, Snapshot: %s. Attached: %s", tag, snap_id, dev_id)
        conn = CloudHost.connect_ec2()
        vol = conn.create_volume(disk_sz_gb, CloudHost.zone(),
                                 snapshot=snap_id,
                                 volume_type='gp2')
                                 # volume_type='io1',
                                 # iops=30*disk_sz_gb)
        CloudHost._wait_for_status(vol, 'available')
        vol_id = vol.id
        EBSVol.log_info("Created volume with id %s", vol_id)

        if tag is not None:
            conn.create_tags([vol_id], {"Name": tag})
            EBSVol.log_info("Added tag %s to volume with id %s", tag, vol_id)

        device_path = EBSVol._attach_free_volume(vol_id, dev_id)
        return device_path, vol_id

    # @staticmethod
    # def detach_mounted_volume(dev_id, mount_dir, delete=False):
    #     CloudHelper.log_info("Detaching volume mounted at device " + dev_id)
    #     vol_id = CloudHelper.get_volume_id_from_device(dev_id)
    #     CloudHelper.log_debug("Device " + dev_id + " maps volume " + vol_id)
    #
    #     # find the instance and device to which the volume is mapped
    #     instance, device = CloudHelper._get_volume_attach_info(vol_id)
    #     if instance is None:  # the volume is not mounted
    #         return
    #
    #     # if mounted to current instance, also unmount the device
    #     if instance == CloudHelper.instance_id():
    #         dev_id = device.split('/')[-1]
    #         CloudHelper.unmount_device(dev_id, mount_dir)
    #         time.sleep(1)
    #
    #     return CloudHelper.detach_volume(vol_id, delete=delete)

    @staticmethod
    def detach_volume(vol_id, delete=False):
        EBSVol.configure_host_commands()
        # find the instance and device to which the volume is mapped
        instance, device = EBSVol._get_volume_attach_info(vol_id)
        conn = CloudHost.connect_ec2()
        if instance is not None:  # the volume is attached
            EBSVol.log_debug("Detaching %s from instance %s device %r", vol_id, instance, device)
            vol = EBSVol.get_volume(vol_id)
            t1 = time.time()
            conn.detach_volume(vol_id, instance, device)
            if not CloudHost._wait_for_status_extended(vol, 'available'):
                raise Exception("Volume could not be detached " + vol_id)
            tdiff = int(time.time() - t1)
            CloudHost.publish_stats("EBSDetachTime", "Count", tdiff)
        if delete:
            EBSVol.log_debug("Deleting %s", vol_id)
            conn.delete_volume(vol_id)

    @staticmethod
    def attach_volume(vol_id, dev_id, force_detach=False):
        """
        Returns the device path where the volume is attached.

        If the volume is already attached to the current instance, the existing device path is returned,
        which may be different from what was requested.

        :param vol_id: EBS volume id to attach
        :param dev_id: volume will be attached at /dev/dev_id
        :param force_detach: detach the volume from any other instance that might have attached it
        :return: device_path
        """
        EBSVol.configure_host_commands()
        EBSVol.log_info("Attaching volume %s to dev_id %s", vol_id, dev_id)
        EBSVol._ensure_volume_available(vol_id, force_detach=force_detach)
        att_instance_id, att_device = EBSVol._get_volume_attach_info(vol_id)

        if att_instance_id is None:
            return EBSVol._attach_free_volume(vol_id, dev_id)
        else:
            EBSVol.log_warn("Volume %s already attached to %s at %s", vol_id, att_instance_id, att_device)
            return att_device

    @staticmethod
    def snapshot_volume(vol_id=None, dev_id=None, tag=None, description=None, wait_till_complete=True):
        EBSVol.configure_host_commands()
        if dev_id is not None:
            vol_id = EBSVol.get_volume_id_from_device(dev_id)
        if vol_id is None:
            EBSVol.log_warn("No volume to snapshot. vol_id: %r, dev_id %r", vol_id, dev_id)
            return
        vol = EBSVol.get_volume(vol_id)
        EBSVol.log_info("Creating snapshot for volume: %s", vol_id)
        snap = vol.create_snapshot(description)
        if wait_till_complete and (not CloudHost._wait_for_status_extended(snap, 'completed')):
            raise Exception("Could not create snapshot for volume " + vol_id)
        EBSVol.log_info("Created snapshot %s for volume %s", snap.id, vol_id)
        if tag is not None:
            CloudHost.connect_ec2().create_tags([snap.id], {'Name': tag})
        return snap.id

    @staticmethod
    def delete_snapshot(snapshot_id):
        CloudHost.connect_ec2().delete_snapshot(snapshot_id)
